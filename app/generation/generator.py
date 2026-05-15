import os
from typing import List, Optional
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
from app.generation.prompt_builder import build_prompt, parse_llm_response
from app.generation.confidence import compute_confidence, should_answer, get_fallback

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

GROQ_MODEL = "llama3-8b-8192"
NVIDIA_MODEL = "meta/llama-3.1-8b-instruct"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"


def get_llm_client():
    if LLM_PROVIDER == "nvidia":
        return OpenAI(api_key=NVIDIA_API_KEY, base_url=NVIDIA_BASE_URL)
    return Groq(api_key=GROQ_API_KEY)


def generate_answer(
    query: str,
    chunks: List[dict],
    top_score: float,
    reranked_count: int,
    doc_id: Optional[str] = None,
) -> dict:
    confidence = compute_confidence(top_score, reranked_count)

    if not should_answer(confidence):
        result = get_fallback()
        result["confidence"] = confidence
        result["doc_id"] = doc_id
        result["prompt_version"] = "v1"
        return result

    prompt_data = build_prompt(query=query, chunks=chunks)

    try:
        client = get_llm_client()

        if LLM_PROVIDER == "nvidia":
            response = client.chat.completions.create(
                model=NVIDIA_MODEL,
                messages=[{"role": "user", "content": prompt_data["system_prompt"]}],
                temperature=0.1,
                max_tokens=1024,
            )
        else:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt_data["system_prompt"]}],
                temperature=0.1,
                max_tokens=1024,
            )

        raw_response = response.choices[0].message.content
        parsed = parse_llm_response(raw_response, chunks)

        return {
            "answer": parsed["answer"],
            "source_chunk_id": parsed["source_chunk_id"],
            "source_text": parsed["source_text"],
            "source_page": parsed["source_page"],
            "confidence": confidence,
            "top_score": top_score,
            "is_fallback": False,
            "doc_id": doc_id,
            "prompt_version": prompt_data["prompt_version"],
            "llm_provider": LLM_PROVIDER,
            "chunks_used": len(chunks),
        }

    except Exception as e:
        result = get_fallback()
        result["error"] = str(e)
        result["doc_id"] = doc_id
        return result