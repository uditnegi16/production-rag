def check_hallucination(answer: str, source_text: str) -> dict:
    if not answer or not source_text:
        return {
            "hallucinated": True,
            "reason": "Missing answer or source text",
            "overlap_score": 0.0,
        }

    answer_words = set(answer.lower().split())
    source_words = set(source_text.lower().split())

    overlap = answer_words & source_words
    overlap_score = round(len(overlap) / max(len(answer_words), 1), 4)

    hallucinated = overlap_score < 0.15

    return {
        "hallucinated": hallucinated,
        "reason": "Low word overlap with source chunk" if hallucinated else "Answer grounded in source",
        "overlap_score": overlap_score,
        "overlap_word_count": len(overlap),
    }


def check_keyword_coverage(answer: str, expected_keywords: list) -> dict:
    answer_lower = answer.lower()
    found = [kw for kw in expected_keywords if kw.lower() in answer_lower]
    missing = [kw for kw in expected_keywords if kw.lower() not in answer_lower]
    coverage = round(len(found) / max(len(expected_keywords), 1), 4)

    return {
        "coverage": coverage,
        "found_keywords": found,
        "missing_keywords": missing,
        "passed": coverage >= 0.5,
    }