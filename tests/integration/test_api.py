import os
import shutil
import pytest
from fastapi.testclient import TestClient
from fpdf import FPDF
from app.api.main import app

TEST_CHROMA_PATH = "./data/processed/chroma_test_api"
TEST_DB = "sqlite:///./data/processed/test_api_logs.db"
TEST_PDF_PATH = "./data/raw/test_api.pdf"

client = TestClient(app)


def create_test_pdf(path: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 10, (
        "This is a test document for API integration testing. "
        "The company reported annual revenue of 10 billion dollars in 2024. "
        "Revenue grew by 15 percent compared to the previous year. "
        "The board approved a dividend of 2 dollars per share. "
        "Operating costs were reduced by 8 percent through efficiency programs."
    ))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pdf.output(path)


@pytest.fixture(autouse=True)
def setup_and_teardown(monkeypatch):
    monkeypatch.setenv("CHROMA_PERSIST_PATH", TEST_CHROMA_PATH)
    monkeypatch.setenv("POSTGRES_URL", TEST_DB)

    import app.ingestion.vector_store as vs
    import app.monitoring.logger as logger_module
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    vs._client = None
    vs._collection = None

    engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
    logger_module.engine = engine
    logger_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger_module.Base.metadata.create_all(bind=engine)

    create_test_pdf(TEST_PDF_PATH)

    yield

    vs._client = None
    vs._collection = None
    logger_module.Base.metadata.drop_all(bind=engine)
    engine.dispose()

    import time
    time.sleep(0.2)

    if os.path.exists(TEST_CHROMA_PATH):
        shutil.rmtree(TEST_CHROMA_PATH)
    if os.path.exists(TEST_PDF_PATH):
        os.remove(TEST_PDF_PATH)
    try:
        if os.path.exists("./data/processed/test_api_logs.db"):
            os.remove("./data/processed/test_api_logs.db")
    except PermissionError:
        pass


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Production RAG API" in response.json()["message"]


def test_upload_rejects_non_pdf():
    response = client.post(
        "/api/v1/upload",
        files={"file": ("test.txt", b"some text content", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_pdf_succeeds():
    with open(TEST_PDF_PATH, "rb") as f:
        response = client.post(
            "/api/v1/upload",
            files={"file": ("test_api.pdf", f, "application/pdf")},
        )
    assert response.status_code == 200
    data = response.json()
    assert "doc_id" in data
    assert data["chunks_stored"] > 0


def test_query_rejects_empty_query():
    response = client.post(
        "/api/v1/query",
        json={"query": ""},
    )
    assert response.status_code == 400


def test_dashboard_returns_data():
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "stats" in data
    assert "recent_logs" in data
    assert "summary" in data


def test_feedback_rejects_invalid_score():
    response = client.post(
        "/api/v1/feedback",
        json={"log_id": "fake-id", "feedback": 0},
    )
    assert response.status_code == 400