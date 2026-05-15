import re
from typing import List


def chunk_document(parsed_doc: dict, chunk_size: int = 512, overlap: int = 50) -> List[dict]:
    chunks = []
    chunk_index = 0

    for page in parsed_doc["pages"]:
        page_chunks = _chunk_text(
            text=page["text"],
            page_number=page["page_number"],
            doc_id=parsed_doc["doc_id"],
            file_name=parsed_doc["file_name"],
            chunk_size=chunk_size,
            overlap=overlap,
            chunk_index_start=chunk_index,
        )
        chunks.extend(page_chunks)
        chunk_index += len(page_chunks)

    return chunks


def _chunk_text(
    text: str,
    page_number: int,
    doc_id: str,
    file_name: str,
    chunk_size: int,
    overlap: int,
    chunk_index_start: int,
) -> List[dict]:
    sentences = _split_into_sentences(text)
    chunks = []
    current_chunk = []
    current_length = 0
    chunk_index = chunk_index_start

    for sentence in sentences:
        sentence_length = len(sentence)

        if current_length + sentence_length > chunk_size and current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(_build_chunk(
                text=chunk_text,
                doc_id=doc_id,
                file_name=file_name,
                page_number=page_number,
                chunk_index=chunk_index,
            ))
            chunk_index += 1

            overlap_text = _get_overlap(current_chunk, overlap)
            current_chunk = overlap_text
            current_length = sum(len(s) for s in current_chunk)

        current_chunk.append(sentence)
        current_length += sentence_length

    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append(_build_chunk(
            text=chunk_text,
            doc_id=doc_id,
            file_name=file_name,
            page_number=page_number,
            chunk_index=chunk_index,
        ))

    return chunks


def _build_chunk(text: str, doc_id: str, file_name: str, page_number: int, chunk_index: int) -> dict:
    return {
        "chunk_id": f"{doc_id}_chunk_{chunk_index}",
        "doc_id": doc_id,
        "file_name": file_name,
        "page_number": page_number,
        "chunk_index": chunk_index,
        "text": text,
        "char_count": len(text),
    }


def _split_into_sentences(text: str) -> List[str]:
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def _get_overlap(sentences: List[str], overlap_chars: int) -> List[str]:
    overlap = []
    total = 0
    for sentence in reversed(sentences):
        if total + len(sentence) > overlap_chars:
            break
        overlap.insert(0, sentence)
        total += len(sentence)
    return overlap