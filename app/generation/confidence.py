CONFIDENCE_THRESHOLD = 0.4
FALLBACK_MESSAGE = (
    "I don't have enough information in the provided document to answer this question confidently. "
    "Please try rephrasing your question or upload a more relevant document."
)


def compute_confidence(top_score: float, reranked_count: int) -> float:
    if reranked_count == 0 or top_score == 0.0:
        return 0.0
    count_factor = min(reranked_count / 3.0, 1.0)
    confidence = round((top_score * 0.7) + (count_factor * 0.3), 4)
    return confidence


def should_answer(confidence: float) -> bool:
    return confidence >= CONFIDENCE_THRESHOLD


def get_fallback() -> dict:
    return {
        "answer": FALLBACK_MESSAGE,
        "confidence": 0.0,
        "citation": None,
        "is_fallback": True,
    }