import pytest
import os
import shutil
from app.ingestion.vector_store import (
    store_chunks,
    search_chunks,
    delete_document,
    get_document_count,
    get_collection,
)

TEST_CHROMA_PATH = "./data/processed/chroma_test"


@pytest.fixture(autouse=True)
def clean_test_db(monkeypatch):
    monkeypatch.setenv("CHROMA_PERSIST_PATH", TEST_CHROMA_PATH)

    import app.ingestion.vector_store as vs
    vs._client = None
    vs._collection = None

    yield

    vs._client = None
    vs._collection = None

    if os.path.exists(TEST_CHROMA_PATH):
        shutil.rmtree(TEST_CHROMA_PATH)


def _make_chunks(n: int, doc_id: str = "test_doc") -> list:
    return [
        {
            "chunk_id": f"{doc_id}_chunk_{i}",
            "doc_id": doc_id,
            "file_name": "test.pdf",
            "page_number": 1,
            "chunk_index": i,
            "text": f"This is test chunk number {i} with some content.",
            "char_count": 40,
            "embedding": [0.1 * (i + 1)] * 384,
            "embedding_model": "all-MiniLM-L6-v2",
        }
        for i in range(n)
    ]


def test_store_chunks_returns_count():
    chunks = _make_chunks(3)
    result = store_chunks(chunks)
    assert result == 3


def test_store_chunks_raises_on_empty():
    with pytest.raises(ValueError):
        store_chunks([])


def test_store_chunks_raises_on_missing_embedding():
    chunks = [{"chunk_id": "x", "doc_id": "d", "file_name": "f.pdf",
               "page_number": 1, "chunk_index": 0, "text": "hi",
               "char_count": 2}]
    with pytest.raises(ValueError):
        store_chunks(chunks)


def test_search_chunks_returns_results():
    chunks = _make_chunks(3)
    store_chunks(chunks)
    query_embedding = [0.1] * 384
    results = search_chunks(query_embedding, top_k=2)
    assert len(results) == 2
    assert "text" in results[0]
    assert "similarity_score" in results[0]


def test_delete_document_removes_chunks():
    chunks = _make_chunks(3, doc_id="doc_to_delete")
    store_chunks(chunks)
    deleted = delete_document("doc_to_delete")
    assert deleted == 3


def test_get_document_count():
    chunks = _make_chunks(4)
    store_chunks(chunks)
    count = get_document_count()
    assert count == 4