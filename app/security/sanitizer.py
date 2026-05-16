import re

INJECTION_PATTERNS = [
    r"ignore (all |previous |prior )?(instructions|rules|prompts)",
    r"you are now",
    r"new instruction",
    r"system prompt",
    r"disregard",
    r"forget (all |everything |prior )",
    r"act as",
    r"pretend (you are|to be)",
]


def sanitize_chunk(text: str) -> str:
    for pattern in INJECTION_PATTERNS:
        text = re.sub(pattern, "[REDACTED]", text, flags=re.IGNORECASE)
    return text


def sanitize_query(query: str) -> str:
    query = query.strip()
    if len(query) > 1000:
        query = query[:1000]
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            raise ValueError("Query contains disallowed content.")
    return query