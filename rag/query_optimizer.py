"""
Query optimization: rewrites casual user queries into a form that
retrieves better from the vector store, and classifies the ticket
category up front.

This is the "Query Agent" from the architecture diagram. It uses the
LLM directly rather than an agent framework — for a single rewrite step,
a raw LLM call is simpler, cheaper, and just as effective as a full
agent loop.
"""

import json

from app.config import TICKET_CATEGORIES
from models.llm_model import get_llm

_REWRITE_SYSTEM_PROMPT = """You are a query optimization assistant for an IT support \
search system. Given a user's informal description of a technical issue, rewrite it \
as a concise, technical search query that will retrieve relevant historical tickets \
and documentation. Keep it to one sentence. Preserve all technical details (product \
names, error messages, codes) exactly. Do not add information that wasn't implied \
by the original query.

Respond with ONLY the rewritten query text, nothing else — no quotes, no preamble."""

_CLASSIFY_SYSTEM_PROMPT = f"""You are a ticket classification assistant. Classify the \
user's issue into exactly one of these categories: {", ".join(TICKET_CATEGORIES)}.

Respond with ONLY valid JSON in this exact format, nothing else:
{{"category": "<one of the categories above>", "confidence": <float between 0 and 1>}}"""


def rewrite_query(raw_query: str) -> str:
    """
    Rewrite a casual query into a more retrieval-friendly form.
    Falls back to the original query if the LLM call fails, so a
    flaky API never breaks retrieval entirely.
    """
    try:
        llm = get_llm()
        rewritten = llm.generate(
            prompt=raw_query,
            system_prompt=_REWRITE_SYSTEM_PROMPT,
            max_tokens=100,
        )
        rewritten = rewritten.strip().strip('"')
        return rewritten if rewritten else raw_query
    except Exception as e:
        print(f"[WARN] Query rewrite failed, using original query: {e}")
        return raw_query


def classify_ticket(query: str) -> dict:
    """
    Classify a query into one of TICKET_CATEGORIES.
    Returns {"category": str, "confidence": float}.
    Falls back to "Other" / 0.0 on any failure.
    """
    try:
        llm = get_llm()
        raw = llm.generate(
            prompt=query,
            system_prompt=_CLASSIFY_SYSTEM_PROMPT,
            max_tokens=60,
        )
        raw = raw.strip()
        # Strip markdown code fences if the model adds them despite instructions
        if raw.startswith("```"):
            raw = raw.strip("`").replace("json", "", 1).strip()
        result = json.loads(raw)
        category = result.get("category", "Other")
        confidence = float(result.get("confidence", 0.0))
        if category not in TICKET_CATEGORIES:
            category = "Other"
        return {"category": category, "confidence": confidence}
    except Exception as e:
        print(f"[WARN] Classification failed: {e}")
        return {"category": "Other", "confidence": 0.0}


def optimize_query(raw_query: str) -> dict:
    """
    Run both rewriting and classification, returning everything the
    retriever and API response need in one call.
    """
    return {
        "original_query": raw_query,
        "rewritten_query": rewrite_query(raw_query),
        "classification": classify_ticket(raw_query),
    }
