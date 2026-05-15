import os
from pathlib import Path
from pypdf import PdfReader
from typing import Optional


def parse_pdf(file_path: str, doc_id: Optional[str] = None) -> dict:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file, got: {path.suffix}")

    reader = PdfReader(str(path))
    total_pages = len(reader.pages)
    pages = []

    for page_num, page in enumerate(reader.pages):
        raw_text = page.extract_text()

        if not raw_text:
            continue

        cleaned_text = _clean_text(raw_text)

        if len(cleaned_text.strip()) < 20:
            continue

        pages.append({
            "page_number": page_num + 1,
            "text": cleaned_text,
            "char_count": len(cleaned_text),
        })

    if not pages:
        raise ValueError("No extractable text found in this PDF.")

    return {
        "doc_id": doc_id or path.stem,
        "file_name": path.name,
        "file_path": str(path),
        "total_pages": total_pages,
        "pages_with_text": len(pages),
        "pages": pages,
    }


def _clean_text(text: str) -> str:
    import re
    text = text.replace("\x00", "")
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)
    text = text.strip()
    return text