import time
import hashlib
from typing import Optional
from app.ingestion.parser import parse_pdf
from app.ingestion.chunker import chunk_document
from app.ingestion.embedder import embed_chunks, validate_embeddings
from app.ingestion.vector_store import store_chunks, delete_document


def run_ingestion(file_path: str, doc_id: Optional[str] = None) -> dict:
    result = {
        "doc_id": None,
        "file_name": None,
        "status": "failed",
        "total_pages": 0,
        "pages_with_text": 0,
        "total_chunks": 0,
        "chunks_stored": 0,
        "duration_seconds": 0.0,
        "error": None,
    }

    start_time = time.time()

    try:
        print(f"[1/4] Parsing PDF: {file_path}")
        parsed = parse_pdf(file_path, doc_id=doc_id)

        result["doc_id"] = parsed["doc_id"]
        result["file_name"] = parsed["file_name"]
        result["total_pages"] = parsed["total_pages"]
        result["pages_with_text"] = parsed["pages_with_text"]

        print(f"[2/4] Chunking document: {parsed['pages_with_text']} pages")
        chunks = chunk_document(parsed, chunk_size=512, overlap=50)
        result["total_chunks"] = len(chunks)

        if not chunks:
            raise ValueError("No chunks produced from document.")

        print(f"[3/4] Embedding {len(chunks)} chunks")
        chunks = embed_chunks(chunks)

        if not validate_embeddings(chunks):
            raise ValueError("Embedding validation failed. Some chunks have invalid embeddings.")

        print(f"[4/4] Storing chunks in ChromaDB")
        delete_document(parsed["doc_id"])
        stored = store_chunks(chunks)
        result["chunks_stored"] = stored

        result["status"] = "success"
        print(f"Done. {stored} chunks stored for doc_id: {parsed['doc_id']}")

    except Exception as e:
        result["error"] = str(e)
        result["status"] = "failed"
        print(f"Ingestion failed: {e}")

    finally:
        result["duration_seconds"] = round(time.time() - start_time, 2)

    return result


def generate_doc_id(file_path: str) -> str:
    with open(file_path, "rb") as f:
        file_hash = hashlib.md5(f.read()).hexdigest()[:8]
    import os
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    return f"{base_name}_{file_hash}"