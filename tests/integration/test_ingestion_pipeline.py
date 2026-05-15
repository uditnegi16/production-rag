import os
import shutil
import pytest
from fpdf import FPDF
from app.ingestion.ingestion_pipeline import run_ingestion, generate_doc_id

TEST_CHROMA_PATH = "./data/processed/chroma_test"
TEST_PDF_PATH = "./data/raw/test_integration.pdf"


def create_test_pdf(path: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, (
        "This is a test document for integration testing. "
        "It contains multiple sentences to ensure chunking works correctly. "
        "The ingestion pipeline should parse this document successfully. "
        "Each sentence adds more content to ensure we get multiple chunks. "
        "The final result should show chunks stored in ChromaDB."
    ))
    pdf.add_page()
    pdf.multi_cell(0, 10, (
        "This is the second page of the test document. "
        "It also contains multiple sentences. "
        "Both pages should be parsed and chunked correctly. "
        "The pipeline should handle multi-page documents without issues."
    ))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pdf.output(path)


@pytest.fixture(autouse=True)
def setup_and_teardown(monkeypatch):
    monkeypatch.setenv("CHROMA_PERSIST_PATH", TEST_CHROMA_PATH)

    import app.ingestion.vector_store as vs
    vs._client = None
    vs._collection = None

    create_test_pdf(TEST_PDF_PATH)

    yield

    vs._client = None
    vs._collection = None

    if os.path.exists(TEST_CHROMA_PATH):
        shutil.rmtree(TEST_CHROMA_PATH)
    if os.path.exists(TEST_PDF_PATH):
        os.remove(TEST_PDF_PATH)


def test_full_ingestion_pipeline_succeeds():
    result = run_ingestion(TEST_PDF_PATH, doc_id="integration_test_doc")
    assert result["status"] == "success"
    assert result["chunks_stored"] > 0
    assert result["total_pages"] == 2
    assert result["error"] is None


def test_ingestion_returns_correct_doc_id():
    result = run_ingestion(TEST_PDF_PATH, doc_id="my_test_doc")
    assert result["doc_id"] == "my_test_doc"


def test_ingestion_fails_on_missing_file():
    result = run_ingestion("nonexistent.pdf")
    assert result["status"] == "failed"
    assert result["error"] is not None


def test_generate_doc_id_is_deterministic():
    id1 = generate_doc_id(TEST_PDF_PATH)
    id2 = generate_doc_id(TEST_PDF_PATH)
    assert id1 == id2


def test_generate_doc_id_contains_filename():
    doc_id = generate_doc_id(TEST_PDF_PATH)
    assert "test_integration" in doc_id