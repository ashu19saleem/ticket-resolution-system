"""
Text preprocessing utilities: cleaning and chunking.

Chunking matters a lot for RAG quality — chunks too large dilute
relevance, chunks too small lose context. CHUNK_SIZE/CHUNK_OVERLAP
are tuned in config.py and can be adjusted without touching this code.
"""

import re
from typing import List

from app.config import CHUNK_SIZE, CHUNK_OVERLAP


def clean_text(text: str) -> str:
    """Normalize whitespace and strip control characters."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[str]:
    """
    Split text into overlapping chunks by character count, breaking on
    sentence boundaries where possible so chunks don't cut mid-sentence.
    """
    text = clean_text(text)
    if len(text) <= chunk_size:
        return [text] if text else []

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= chunk_size:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            # start new chunk with overlap from the end of the previous one
            overlap_text = current[-chunk_overlap:] if current else ""
            current = f"{overlap_text} {sentence}".strip()

    if current:
        chunks.append(current)

    return chunks


def format_ticket_for_embedding(ticket: dict) -> str:
    """
    Turn a structured ticket row into a single text blob optimized for
    semantic search. Putting description + resolution together means a
    query about a problem can retrieve tickets whose *resolution* text
    is also relevant, not just the description.
    """
    return (
        f"Category: {ticket.get('category', '')}. "
        f"Issue: {ticket.get('description', '')}. "
        f"Resolution: {ticket.get('resolution', '')}"
    )
