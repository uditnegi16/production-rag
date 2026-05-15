from app.monitoring.logger import get_stats, get_recent_logs


def get_dashboard_data(limit: int = 100) -> dict:
    stats = get_stats()
    logs = get_recent_logs(limit=limit)

    failed_queries = [l for l in logs if l["is_fallback"] or l["error"]]
    hallucinated_queries = [l for l in logs if l["hallucination_flag"]]
    negative_feedback = [l for l in logs if l["user_feedback"] == -1]

    return {
        "stats": stats,
        "recent_logs": logs,
        "failed_queries": failed_queries,
        "hallucinated_queries": hallucinated_queries,
        "negative_feedback_queries": negative_feedback,
        "summary": {
            "total_queries": stats["total_queries"],
            "fallback_rate_pct": round(stats["fallback_rate"] * 100, 2),
            "hallucination_rate_pct": round(stats["hallucination_rate"] * 100, 2),
            "latency_p50_ms": stats["latency_p50_ms"],
            "latency_p95_ms": stats["latency_p95_ms"],
            "avg_confidence": stats["avg_confidence"],
        }
    }