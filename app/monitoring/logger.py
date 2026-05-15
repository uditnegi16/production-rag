import os
import time
import uuid
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

POSTGRES_URL = os.getenv("POSTGRES_URL", "sqlite:///./data/processed/rag_logs.db")

engine = create_engine(POSTGRES_URL, connect_args={"check_same_thread": False} if "sqlite" in POSTGRES_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow)
    query_text = Column(Text, nullable=False)
    doc_id = Column(String, nullable=True)
    answer = Column(Text, nullable=True)
    source_chunk_id = Column(String, nullable=True)
    source_page = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    top_score = Column(Float, nullable=True)
    is_fallback = Column(Boolean, default=False)
    hallucination_flag = Column(Boolean, default=False)
    latency_ms = Column(Float, nullable=True)
    chunks_retrieved = Column(Integer, nullable=True)
    chunks_reranked = Column(Integer, nullable=True)
    llm_provider = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)
    user_feedback = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)


def log_query(
    query_text: str,
    answer: str,
    doc_id: Optional[str] = None,
    source_chunk_id: Optional[str] = None,
    source_page: Optional[int] = None,
    confidence: Optional[float] = None,
    top_score: Optional[float] = None,
    is_fallback: bool = False,
    latency_ms: Optional[float] = None,
    chunks_retrieved: Optional[int] = None,
    chunks_reranked: Optional[int] = None,
    llm_provider: Optional[str] = None,
    prompt_version: Optional[str] = None,
    error: Optional[str] = None,
) -> str:
    init_db()
    log_id = str(uuid.uuid4())

    db = SessionLocal()
    try:
        log_entry = QueryLog(
            id=log_id,
            query_text=query_text,
            doc_id=doc_id,
            answer=answer,
            source_chunk_id=source_chunk_id,
            source_page=source_page,
            confidence=confidence,
            top_score=top_score,
            is_fallback=is_fallback,
            latency_ms=latency_ms,
            chunks_retrieved=chunks_retrieved,
            chunks_reranked=chunks_reranked,
            llm_provider=llm_provider,
            prompt_version=prompt_version,
            error=error,
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

    return log_id


def log_feedback(log_id: str, feedback: int):
    db = SessionLocal()
    try:
        entry = db.query(QueryLog).filter(QueryLog.id == log_id).first()
        if entry:
            entry.user_feedback = feedback
            db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_recent_logs(limit: int = 100) -> list:
    init_db()
    db = SessionLocal()
    try:
        logs = db.query(QueryLog).order_by(QueryLog.timestamp.desc()).limit(limit).all()
        return [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "query_text": log.query_text,
                "doc_id": log.doc_id,
                "answer": log.answer,
                "source_chunk_id": log.source_chunk_id,
                "source_page": log.source_page,
                "confidence": log.confidence,
                "top_score": log.top_score,
                "is_fallback": log.is_fallback,
                "hallucination_flag": log.hallucination_flag,
                "latency_ms": log.latency_ms,
                "chunks_retrieved": log.chunks_retrieved,
                "chunks_reranked": log.chunks_reranked,
                "llm_provider": log.llm_provider,
                "prompt_version": log.prompt_version,
                "user_feedback": log.user_feedback,
                "error": log.error,
            }
            for log in logs
        ]
    finally:
        db.close()


def get_stats() -> dict:
    init_db()
    db = SessionLocal()
    try:
        total = db.query(QueryLog).count()
        fallbacks = db.query(QueryLog).filter(QueryLog.is_fallback == True).count()
        hallucinations = db.query(QueryLog).filter(QueryLog.hallucination_flag == True).count()

        latencies = db.query(QueryLog.latency_ms).filter(QueryLog.latency_ms != None).all()
        latency_values = sorted([l[0] for l in latencies])

        p50 = _percentile(latency_values, 50)
        p95 = _percentile(latency_values, 95)

        confidences = db.query(QueryLog.confidence).filter(QueryLog.confidence != None).all()
        avg_confidence = round(
            sum(c[0] for c in confidences) / len(confidences), 4
        ) if confidences else 0.0

        return {
            "total_queries": total,
            "fallback_count": fallbacks,
            "fallback_rate": round(fallbacks / total, 4) if total > 0 else 0.0,
            "hallucination_count": hallucinations,
            "hallucination_rate": round(hallucinations / total, 4) if total > 0 else 0.0,
            "latency_p50_ms": p50,
            "latency_p95_ms": p95,
            "avg_confidence": avg_confidence,
        }
    finally:
        db.close()


def _percentile(values: list, percent: int) -> Optional[float]:
    if not values:
        return None
    index = int(len(values) * percent / 100)
    index = min(index, len(values) - 1)
    return round(values[index], 2)