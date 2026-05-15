from app.ingestion.chunker import chunk_document, _split_into_sentences, _get_overlap


def test_split_into_sentences_basic():
    text = "This is sentence one. This is sentence two. And three."
    result = _split_into_sentences(text)
    assert len(result) == 3


def test_get_overlap_returns_tail_sentences():
    sentences = ["Short one.", "Another sentence here.", "Final sentence."]
    overlap = _get_overlap(sentences, overlap_chars=40)
    assert len(overlap) > 0
    assert overlap[-1] == "Final sentence."


def test_chunk_document_produces_chunks():
    parsed_doc = {
        "doc_id": "test_doc",
        "file_name": "test.pdf",
        "pages": [
            {
                "page_number": 1,
                "text": "This is sentence one. This is sentence two. This is sentence three. This is sentence four. This is sentence five.",
                "char_count": 110,
            }
        ]
    }
    chunks = chunk_document(parsed_doc, chunk_size=80, overlap=20)
    assert len(chunks) > 1
    assert chunks[0]["doc_id"] == "test_doc"
    assert chunks[0]["page_number"] == 1
    assert "chunk_0" in chunks[0]["chunk_id"]


def test_chunk_ids_are_unique():
    parsed_doc = {
        "doc_id": "test_doc",
        "file_name": "test.pdf",
        "pages": [
            {
                "page_number": 1,
                "text": "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five. Sentence six.",
                "char_count": 90,
            },
            {
                "page_number": 2,
                "text": "Sentence seven. Sentence eight. Sentence nine. Sentence ten. Sentence eleven.",
                "char_count": 75,
            }
        ]
    }
    chunks = chunk_document(parsed_doc, chunk_size=60, overlap=10)
    ids = [c["chunk_id"] for c in chunks]
    assert len(ids) == len(set(ids))