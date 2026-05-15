from typing import List
from pathlib import Path

PROMPT_VERSION = "v1"
PROMPT_PATH = Path("prompts/rag_prompt_v1.txt")

SYSTEM_PROMPT = """You are a precise document question-answering assistant.

STRICT RULES:
1. Answer ONLY using the context provided below. Do not use any outside knowledge.
2. After your answer, you MUST cite the exact chunk ID you used as your source.
3. If the context does not contain enough information to answer, say exactly: "I don't know based on the provided context."
4. Never speculate, infer beyond what is written, or make up information.
5. Keep your answer concise and directly responsive to the question.

CONTEXT:
{context}

QUESTION:
{question}

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
ANSWER: [your answer here]
SOURCE: [chunk_id of the chunk you used]"""


def build_prompt(query: str, chunks: List[dict]) -> dict:
    if not chunks:
        raise ValueError("Cannot build prompt with no chunks.")
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    context_parts = []
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id", "unknown")
        page = chunk.get("metadata", {}).get("page_number", "?")
        text = chunk.get("text", "")
        context_parts.append(f"[{chunk_id}] (page {page}):\n{text}")

    context = "\n\n---\n\n".join(context_parts)

    filled_prompt = SYSTEM_PROMPT.format(
        context=context,
        question=query,
    )

    _save_prompt_to_file(filled_prompt)

    return {
        "system_prompt": filled_prompt,
        "context": context,
        "chunk_ids_used": [c.get("chunk_id") for c in chunks],
        "prompt_version": PROMPT_VERSION,
    }


def _save_prompt_to_file(prompt: str):
    try:
        PROMPT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PROMPT_PATH, "w", encoding="utf-8") as f:
            f.write(prompt)
    except Exception:
        pass


def parse_llm_response(response_text: str, chunks: List[dict]) -> dict:
    answer = None
    source_chunk_id = None

    for line in response_text.strip().split("\n"):
        if line.startswith("ANSWER:"):
            answer = line.replace("ANSWER:", "").strip()
        elif line.startswith("SOURCE:"):
            source_chunk_id = line.replace("SOURCE:", "").strip()

    if not answer:
        answer = response_text.strip()

    source_chunk = None
    if source_chunk_id:
        for chunk in chunks:
            if chunk.get("chunk_id") == source_chunk_id:
                source_chunk = chunk
                break

    if not source_chunk and chunks:
        source_chunk = chunks[0]

    return {
        "answer": answer,
        "source_chunk_id": source_chunk_id,
        "source_text": source_chunk.get("text") if source_chunk else None,
        "source_page": source_chunk.get("metadata", {}).get("page_number") if source_chunk else None,
    }