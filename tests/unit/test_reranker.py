import pytest
from app.retrieval.reranker import rerank_chunks, get_top_score


def _make_chunks(texts: list) -> list:
    return [
        {
            "chunk_id": f"doc_chunk_{i}",
            "text": text,
            "similarity_score": 0.8,
            "metadata": {"page_number": 1},
        }
        for i, text in enumerate(texts)
    ]


def test_rerank_chunks_returns_sorted_by_score():
    chunks = _make_chunks([
        "The company revenue was 5 billion dollars in 2023.",
        "The weather in Paris is usually mild in spring.",
        "Total annual revenue grew by 12 percent year over year.",
    ])
    result = rerank_chunks("What was the company revenue?", chunks, top_n=3)
    if len(result) > 1:
        assert result[0]["reranker_score"] >= result[1]["reranker_score"]


def test_rerank_chunks_raises_on_empty_chunks():
    with pytest.raises(ValueError):
        rerank_chunks("some query", [])


def test_rerank_chunks_raises_on_empty_query():
    chunks = _make_chunks(["some text"])
    with pytest.raises(ValueError):
        rerank_chunks("", chunks)


def test_get_top_score_returns_max():
    chunks = [
        {"reranker_score": 0.4},
        {"reranker_score": 0.9},
        {"reranker_score": 0.6},
    ]
    assert get_top_score(chunks) == 0.9


def test_get_top_score_returns_zero_on_empty():
    assert get_top_score([]) == 0.0