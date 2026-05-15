from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np

_model = None
MODEL_NAME = "all-MiniLM-L6-v2"


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_chunks(chunks: List[dict]) -> List[dict]:
    if not chunks:
        raise ValueError("No chunks provided to embed.")

    model = get_model()
    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    for i, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[i].tolist()
        chunk["embedding_model"] = MODEL_NAME

    return chunks


def embed_query(query: str) -> List[float]:
    if not query or not query.strip():
        raise ValueError("Query text cannot be empty.")

    model = get_model()
    embedding = model.encode(query, convert_to_numpy=True)
    return embedding.tolist()


def validate_embeddings(chunks: List[dict]) -> bool:
    for chunk in chunks:
        if "embedding" not in chunk:
            return False
        if not isinstance(chunk["embedding"], list):
            return False
        if len(chunk["embedding"]) == 0:
            return False
        if any(np.isnan(v) for v in chunk["embedding"]):
            return False
    return True