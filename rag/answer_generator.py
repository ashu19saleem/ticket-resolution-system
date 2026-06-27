"""
Answer generation: takes retrieved context + the user's query and asks
the LLM to produce a grounded resolution, then attaches a confidence
score derived from retrieval similarity (not just the LLM's say-so —
LLMs are notoriously overconfident about their own correctness).
"""

from app.config import MIN_RELEVANCE_THRESHOLD
from models.llm_model import get_llm

_ANSWER_SYSTEM_PROMPT = """You are an IT support resolution assistant. You will be \
given a user's issue and a set of retrieved historical tickets and documentation \
excerpts. Using ONLY the information in the provided context, write a clear, \
step-by-step resolution.

Rules:
- Base your answer strictly on the provided context. Do not invent steps that \
aren't supported by it.
- If the context is insufficient to fully resolve the issue, say so explicitly \
and suggest what additional information or escalation would help.
- Write actionable steps, not vague advice.
- Do not mention "the context" or "the documents" in your answer — write as if \
you simply know the resolution.
"""


def _build_context_block(retrieved: list[dict]) -> str:
    """Format retrieved chunks into a numbered context block for the prompt."""
    lines = []
    for i, item in enumerate(retrieved, start=1):
        if item["source_type"] == "ticket":
            lines.append(
                f"[{i}] Historical Ticket {item['source']} "
                f"(category: {item['metadata'].get('category', 'N/A')}): {item['text']}"
            )
        else:
            lines.append(f"[{i}] Documentation ({item['source']}): {item['text']}")
    return "\n\n".join(lines)


def compute_confidence(retrieved: list[dict]) -> float:
    """
    Confidence score derived from retrieval similarity, not the LLM.
    Weighted toward the top result but accounts for how many results
    cleared the relevance bar — one strong match plus supporting
    context scores higher than one strong match alone.
    """
    if not retrieved:
        return 0.0

    relevant = [r for r in retrieved if r["similarity"] >= MIN_RELEVANCE_THRESHOLD]
    if not relevant:
        return round(retrieved[0]["similarity"] * 0.5, 4)  # weak signal only

    top_score = relevant[0]["similarity"]
    support_bonus = min(0.1, 0.02 * (len(relevant) - 1))  # up to +0.1 for corroboration
    confidence = min(1.0, top_score + support_bonus)
    return round(confidence, 4)


def generate_answer(query: str, retrieved: list[dict]) -> dict:
    """
    Generate a grounded answer from retrieved context.

    Returns:
        {
            "answer": str,
            "confidence": float,        # 0-1
            "confidence_label": str,    # "High" | "Medium" | "Low"
            "sources": list[dict],      # [{source, source_type, similarity}]
        }
    """
    confidence = compute_confidence(retrieved)

    if not retrieved:
        return {
            "answer": (
                "No similar historical tickets or documentation were found for this "
                "issue. Consider escalating to a senior engineer or adding this case "
                "to the knowledge base once resolved."
            ),
            "confidence": 0.0,
            "confidence_label": "Low",
            "sources": [],
        }

    context_block = _build_context_block(retrieved)
    prompt = f"User Issue: {query}\n\nRetrieved Context:\n{context_block}\n\nResolution:"

    llm = get_llm()
    answer = llm.generate(
        prompt=prompt,
        system_prompt=_ANSWER_SYSTEM_PROMPT,
        max_tokens=600,
    )

    if confidence >= 0.7:
        label = "High"
    elif confidence >= 0.4:
        label = "Medium"
    else:
        label = "Low"

    sources = [
        {
            "source": r["source"],
            "source_type": r["source_type"],
            "similarity": r["similarity"],
        }
        for r in retrieved
    ]

    return {
        "answer": answer.strip(),
        "confidence": confidence,
        "confidence_label": label,
        "sources": sources,
    }


def summarize_ticket(text: str) -> str:
    """
    Condense a long incident report into a short summary.
    Used by the /summarize endpoint.
    """
    llm = get_llm()
    return llm.generate(
        prompt=text,
        system_prompt=(
            "Summarize the following IT incident report in 2-3 concise sentences. "
            "Preserve key technical details (error messages, affected systems). "
            "Respond with only the summary."
        ),
        max_tokens=200,
    ).strip()
