import os
import pytest
from app.monitoring.logger import log_query, log_feedback, get_recent_logs, get_stats, init_db

TEST_DB = "sqlite:///./data/processed/test_logs.db"


@pytest.fixture(autouse=True)
def use_test_db(monkeypatch):
    monkeypatch.setenv("POSTGRES_URL", TEST_DB)

    import app.monitoring.logger as logger_module
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
    logger_module.engine = engine
    logger_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger_module.Base.metadata.create_all(bind=engine)

    yield

    logger_module.Base.metadata.drop_all(bind=engine)
    engine.dispose()

    import time
    time.sleep(0.1)

    if os.path.exists("./data/processed/test_logs.db"):
        try:
            os.remove("./data/processed/test_logs.db")
        except PermissionError:
            pass


def test_log_query_returns_id():
    log_id = log_query(
        query_text="What is revenue?",
        answer="Revenue was 5 billion.",
        confidence=0.85,
        is_fallback=False,
        latency_ms=320.5,
    )
    assert isinstance(log_id, str)
    assert len(log_id) > 0


def test_get_recent_logs_returns_entries():
    log_query(query_text="Test query", answer="Test answer", latency_ms=100.0)
    logs = get_recent_logs(limit=10)
    assert len(logs) >= 1
    assert logs[0]["query_text"] == "Test query"


def test_log_feedback_updates_entry():
    log_id = log_query(query_text="Test query", answer="Test answer")
    log_feedback(log_id, feedback=-1)
    logs = get_recent_logs(limit=10)
    matching = [l for l in logs if l["id"] == log_id]
    assert matching[0]["user_feedback"] == -1


def test_get_stats_returns_correct_structure():
    log_query(query_text="q1", answer="a1", is_fallback=False, latency_ms=200.0)
    log_query(query_text="q2", answer="fallback", is_fallback=True, latency_ms=50.0)
    stats = get_stats()
    assert "total_queries" in stats
    assert "fallback_rate" in stats
    assert "latency_p50_ms" in stats
    assert "latency_p95_ms" in stats
    assert stats["total_queries"] == 2
    assert stats["fallback_count"] == 1