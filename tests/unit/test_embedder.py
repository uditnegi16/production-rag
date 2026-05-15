import pytest
from app.ingestion.embedder import embed_query, validate_embeddings, embed_chunks


def test_embed_query_returns_list():
    result = embed_query("What is the revenue of the company?")
    assert isinstance(result, list)
    assert len(result) == 384


def test_embed_query_raises_on_empty():
    with pytest.raises(ValueError):
        embed_query("")


def test_embed_query_raises_on_whitespace():
    with pytest.raises(ValueError):
        embed_query("   ")


def test_validate_embeddings_passes_valid():
    chunks = [
        {"text": "hello", "embedding": [0.1, 0.2, 0.3]},
        {"text": "world", "embedding": [0.4, 0.5, 0.6]},
    ]
    assert validate_embeddings(chunks) is True


def test_validate_embeddings_fails_missing():
    chunks = [{"text": "hello"}]
    assert validate_embeddings(chunks) is False


def test_embed_chunks_adds_embedding_field():
    chunks = [
        {"text": "This is the first test chunk.", "chunk_id": "doc_chunk_0"},
        {"text": "This is the second test chunk.", "chunk_id": "doc_chunk_1"},
    ]
    result = embed_chunks(chunks)
    assert "embedding" in result[0]
    assert "embedding_model" in result[0]
    assert len(result[0]["embedding"]) == 384