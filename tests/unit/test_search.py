import pytest
from unittest.mock import patch, MagicMock
from app.retrieval.search import retrieve


def _mock_chunks():
    return [
        {
            "chunk_id": "doc_chunk_0",
            "text": "The company revenue was 5 billion dollars.",
            "similarity_score": 0.85,
            "metadata": {"page_number": 1},
        },
        {
            "chunk_id": "doc_chunk_1",
            "text": "Revenue grew by 12 percent year over year.",
            "similarity_score": 0.80,
            "metadata": {"page_number": 2},
        },
    ]


def test_retrieve_raises_on_empty_query():
    with pytest.raises(ValueError):
        retrieve("")


def test_retrieve_raises_on_whitespace_query():
    with pytest.raises(ValueError):
        retrieve("   ")


@patch("app.retrieval.search.embed_query")
@patch("app.retrieval.search.search_chunks")
@patch("app.retrieval.search.rerank_chunks")
@patch("app.retrieval.search.get_top_score")
def test_retrieve_returns_correct_structure(
    mock_top_score, mock_rerank, mock_search, mock_embed
):
    mock_embed.return_value = [0.1] * 384
    mock_search.return_value = _mock_chunks()
    mock_rerank.return_value = _mock_chunks()
    mock_top_score.return_value = 0.85

    result = retrieve("What was the revenue?", doc_id="test_doc")

    assert "query" in result
    assert "chunks" in result
    assert "top_score" in result
    assert "retrieval_count" in result
    assert "reranked_count" in result
    assert result["retrieval_count"] == 2


@patch("app.retrieval.search.embed_query")
@patch("app.retrieval.search.search_chunks")
def test_retrieve_returns_empty_when_no_chunks(mock_search, mock_embed):
    mock_embed.return_value = [0.1] * 384
    mock_search.return_value = []

    result = retrieve("What was the revenue?")

    assert result["chunks"] == []
    assert result["top_score"] == 0.0