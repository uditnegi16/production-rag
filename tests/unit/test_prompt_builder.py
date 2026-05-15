import pytest
from app.generation.prompt_builder import build_prompt, parse_llm_response


def _make_chunks():
    return [
        {
            "chunk_id": "doc_chunk_0",
            "text": "Revenue was 5 billion dollars in 2023.",
            "metadata": {"page_number": 1},
            "reranker_score": 0.9,
        },
        {
            "chunk_id": "doc_chunk_1",
            "text": "The company grew by 12 percent.",
            "metadata": {"page_number": 2},
            "reranker_score": 0.7,
        },
    ]


def test_build_prompt_raises_on_empty_chunks():
    with pytest.raises(ValueError):
        build_prompt("What is revenue?", [])


def test_build_prompt_raises_on_empty_query():
    with pytest.raises(ValueError):
        build_prompt("", _make_chunks())


def test_build_prompt_contains_query():
    result = build_prompt("What is revenue?", _make_chunks())
    assert "What is revenue?" in result["system_prompt"]


def test_build_prompt_contains_chunk_ids():
    result = build_prompt("What is revenue?", _make_chunks())
    assert "doc_chunk_0" in result["system_prompt"]
    assert "doc_chunk_1" in result["system_prompt"]


def test_parse_llm_response_extracts_answer_and_source():
    response = "ANSWER: Revenue was 5 billion.\nSOURCE: doc_chunk_0"
    result = parse_llm_response(response, _make_chunks())
    assert result["answer"] == "Revenue was 5 billion."
    assert result["source_chunk_id"] == "doc_chunk_0"


def test_parse_llm_response_falls_back_to_first_chunk():
    response = "ANSWER: Revenue was 5 billion.\nSOURCE: unknown_chunk"
    result = parse_llm_response(response, _make_chunks())
    assert result["source_text"] is not None