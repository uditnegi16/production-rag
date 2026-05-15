import pytest
from app.ingestion.parser import parse_pdf, _clean_text


def test_clean_text_removes_extra_whitespace():
    result = _clean_text("hello   world\n\nthis  is   a test")
    assert result == "hello world this is a test"


def test_clean_text_fixes_hyphen_breaks():
    result = _clean_text("manage-\nment system")
    assert result == "management system"


def test_parse_pdf_raises_on_missing_file():
    with pytest.raises(FileNotFoundError):
        parse_pdf("nonexistent.pdf")


def test_parse_pdf_raises_on_wrong_extension():
    with pytest.raises(ValueError):
        parse_pdf("tests/unit/test_parser.py")