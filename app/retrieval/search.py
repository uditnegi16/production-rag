from typing import List, Optional
from app.ingestion.embedder import embed_query
from app.ingestion.vector_store import search_chunks
from app.retrieval.reranker import rerank_chunks, get_top_score


def retrieve(
    query: str,
    doc_id: Optional[str] = None,
    top_k: int = 10,
    top_n: int = 5,
) -> dict:
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    query_embedding = embed_query(query)

    raw_chunks = search_chunks(
        query_embedding=query_embedding,
        top_k=top_k,
        doc_id=doc_id,
    )

    if not raw_chunks:
        return {
            "query": query,
            "chunks": [],
            "top_score": 0.0,
            "retrieval_count": 0,
            "reranked_count": 0,
        }

    reranked_chunks = rerank_chunks(query=query, chunks=raw_chunks, top_n=top_n)
    top_score = get_top_score(reranked_chunks)

    return {
        "query": query,
        "chunks": reranked_chunks,
        "top_score": top_score,
        "retrieval_count": len(raw_chunks),
        "reranked_count": len(reranked_chunks),
    }