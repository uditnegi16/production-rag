from app.generation.confidence import compute_confidence, should_answer, get_fallback


def test_compute_confidence_zero_when_no_chunks():
    assert compute_confidence(0.0, 0) == 0.0


def test_compute_confidence_zero_when_zero_score():
    assert compute_confidence(0.0, 5) == 0.0


def test_compute_confidence_high_with_good_score_and_chunks():
    score = compute_confidence(0.9, 3)
    assert score > 0.7


def test_compute_confidence_lower_with_one_chunk():
    score_one = compute_confidence(0.9, 1)
    score_three = compute_confidence(0.9, 3)
    assert score_one < score_three


def test_should_answer_true_above_threshold():
    assert should_answer(0.5) is True


def test_should_answer_false_below_threshold():
    assert should_answer(0.2) is False


def test_get_fallback_structure():
    result = get_fallback()
    assert result["is_fallback"] is True
    assert result["confidence"] == 0.0
    assert result["citation"] is None
    assert len(result["answer"]) > 0