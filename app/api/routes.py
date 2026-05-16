import time
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from app.ingestion.ingestion_pipeline import run_ingestion, generate_doc_id
from app.retrieval.search import retrieve
from app.generation.generator import generate_answer
from app.monitoring.logger import log_query, log_feedback, init_db
from app.monitoring.dashboard import get_dashboard_data
from app.security.sanitizer import sanitize_query

router = APIRouter()
UPLOAD_DIR = "./data/raw"


class QueryRequest(BaseModel):
    query: str
    doc_id: Optional[str] = None
    top_k: int = 10
    top_n: int = 5


class FeedbackRequest(BaseModel):
    log_id: str
    feedback: int


@router.on_event("startup")
async def startup():
    init_db()
    os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    doc_id = generate_doc_id(file_path)
    result = run_ingestion(file_path=file_path, doc_id=doc_id)

    if result["status"] == "failed":
        raise HTTPException(status_code=500, detail=result["error"])

    return JSONResponse(content={
        "message": "Document ingested successfully.",
        "doc_id": result["doc_id"],
        "file_name": result["file_name"],
        "total_pages": result["total_pages"],
        "chunks_stored": result["chunks_stored"],
        "duration_seconds": result["duration_seconds"],
    })


@router.post("/query")
async def query_document(request: QueryRequest):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    start_time = time.time()

    try:
        clean_query = sanitize_query(request.query)

        retrieval_result = retrieve(
            query=clean_query,
            doc_id=request.doc_id,
            top_k=request.top_k,
            top_n=request.top_n,
        )

        generation_result = generate_answer(
            query=clean_query,
            chunks=retrieval_result["chunks"],
            top_score=retrieval_result["top_score"],
            reranked_count=retrieval_result["reranked_count"],
            doc_id=request.doc_id,
        )

        latency_ms = round((time.time() - start_time) * 1000, 2)

        log_id = log_query(
            query_text=clean_query,
            answer=generation_result.get("answer", ""),
            doc_id=request.doc_id,
            source_chunk_id=generation_result.get("source_chunk_id"),
            source_page=generation_result.get("source_page"),
            confidence=generation_result.get("confidence"),
            top_score=generation_result.get("top_score"),
            is_fallback=generation_result.get("is_fallback", False),
            latency_ms=latency_ms,
            chunks_retrieved=retrieval_result.get("retrieval_count"),
            chunks_reranked=retrieval_result.get("reranked_count"),
            llm_provider=generation_result.get("llm_provider"),
            prompt_version=generation_result.get("prompt_version"),
            error=generation_result.get("error"),
        )

        return JSONResponse(content={
            "log_id": log_id,
            "query": clean_query,
            "answer": generation_result.get("answer"),
            "source_chunk_id": generation_result.get("source_chunk_id"),
            "source_text": generation_result.get("source_text"),
            "source_page": generation_result.get("source_page"),
            "confidence": generation_result.get("confidence"),
            "is_fallback": generation_result.get("is_fallback", False),
            "latency_ms": latency_ms,
            "llm_provider": generation_result.get("llm_provider"),
        })

    except Exception as e:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        log_query(
            query_text=request.query,
            answer="",
            error=str(e),
            latency_ms=latency_ms,
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    if request.feedback not in [-1, 1]:
        raise HTTPException(status_code=400, detail="Feedback must be 1 (positive) or -1 (negative).")
    try:
        log_feedback(request.log_id, request.feedback)
        return {"message": "Feedback recorded."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def dashboard(limit: int = 100):
    try:
        data = get_dashboard_data(limit=limit)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))