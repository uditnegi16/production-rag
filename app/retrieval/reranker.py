from sentence_transformers import CrossEncoder
from typing import List
import torch

_reranker_model = None
RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
RELEVANCE_THRESHOLD = 0.5


def get_reranker() -> CrossEncoder:
    global _reranker_model
    if _reranker_model is None:
        _reranker_model = CrossEncoder(RERANKER_MODEL_NAME)
    return _reranker_model



def rerank_chunks(query: str, chunks: List[dict], top_n: int = 5) -> List[dict]:
    if not chunks:
        raise ValueError("No chunks provided to rerank.")
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    reranker = get_reranker()
    pairs = [[query, chunk["text"]] for chunk in chunks]
    scores = reranker.predict(pairs)

    # normalize raw logits to 0-1 using sigmoid
    import numpy as np
    def sigmoid(x):
        return 1 / (1 + np.exp(-x))

    normalized_scores = sigmoid(scores)

    for i, chunk in enumerate(chunks):
        chunk["reranker_score"] = round(float(normalized_scores[i]), 4)

    ranked = sorted(chunks, key=lambda x: x["reranker_score"], reverse=True)
    filtered = [c for c in ranked if c["reranker_score"] >= RELEVANCE_THRESHOLD]
    return filtered[:top_n]

def get_top_score(chunks: List[dict]) -> float:
    if not chunks:
        return 0.0
    return max(c.get("reranker_score", 0.0) for c in chunks)