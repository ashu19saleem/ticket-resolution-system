"""
Ingestion pipeline: reads tickets.csv + documents/manuals, chunks them,
embeds them, and writes everything into the vector store (ChromaDB).

Run directly to (re)build the vector store:
    python -m rag.ingestion
"""

import csv
import uuid

import chromadb

from app.config import (
    TICKETS_CSV,
    DOCUMENTS_DIR,
    MANUALS_DIR,
    CHROMA_PERSIST_DIR,
    COLLECTION_NAME,
)
from models.embedding_model import get_embedding_model
from utils.preprocess import chunk_text, format_ticket_for_embedding
from utils.document_loader import load_documents_from_dir


def _get_chroma_collection():
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def load_tickets() -> list[dict]:
    """Read tickets.csv into a list of dicts."""
    if not TICKETS_CSV.exists():
        print(f"[WARN] No tickets file found at {TICKETS_CSV}")
        return []

    with open(TICKETS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def build_ticket_records(tickets: list[dict]) -> tuple[list[str], list[str], list[dict]]:
    """
    Convert tickets into (ids, texts, metadatas) ready for embedding.
    One record per ticket — tickets are short enough not to need chunking.
    """
    ids, texts, metadatas = [], [], []
    for ticket in tickets:
        text = format_ticket_for_embedding(ticket)
        ids.append(f"ticket-{ticket.get('ticket_id', uuid.uuid4().hex[:8])}")
        texts.append(text)
        metadatas.append({
            "source_type": "ticket",
            "source": ticket.get("ticket_id", "unknown"),
            "category": ticket.get("category", ""),
            "priority": ticket.get("priority", ""),
            "resolution": ticket.get("resolution", ""),
        })
    return ids, texts, metadatas


def build_document_records(documents: list[dict]) -> tuple[list[str], list[str], list[dict]]:
    """
    Convert loaded documents into chunked (ids, texts, metadatas).
    Documents ARE chunked since manuals/PDFs are typically much longer
    than a single ticket description.
    """
    ids, texts, metadatas = [], [], []
    for doc in documents:
        chunks = chunk_text(doc["text"])
        for i, chunk in enumerate(chunks):
            ids.append(f"doc-{doc['source']}-{i}")
            texts.append(chunk)
            metadatas.append({
                "source_type": "document",
                "source": doc["source"],
                "chunk_index": i,
            })
    return ids, texts, metadatas


def ingest_all(reset: bool = True) -> dict:
    """
    Full ingestion run: tickets + documents + manuals -> embeddings -> ChromaDB.
    Returns a summary dict for logging/API responses.
    """
    collection = _get_chroma_collection()

    if reset:
        # Wipe and rebuild so re-running ingestion doesn't create duplicates
        existing_ids = collection.get()["ids"]
        if existing_ids:
            collection.delete(ids=existing_ids)

    embedder = get_embedding_model()

    tickets = load_tickets()
    docs = load_documents_from_dir(DOCUMENTS_DIR) + load_documents_from_dir(MANUALS_DIR)

    ticket_ids, ticket_texts, ticket_meta = build_ticket_records(tickets)
    doc_ids, doc_texts, doc_meta = build_document_records(docs)

    all_ids = ticket_ids + doc_ids
    all_texts = ticket_texts + doc_texts
    all_meta = ticket_meta + doc_meta

    if not all_ids:
        print("[WARN] Nothing to ingest. Add data to data/tickets.csv or data/documents/.")
        return {"tickets_ingested": 0, "document_chunks_ingested": 0}

    embeddings = embedder.embed_texts(all_texts)

    # Chroma needs batched adds for very large sets; fine in one call for this scale
    collection.add(
        ids=all_ids,
        embeddings=embeddings,
        documents=all_texts,
        metadatas=all_meta,
    )

    summary = {
        "tickets_ingested": len(ticket_ids),
        "document_chunks_ingested": len(doc_ids),
        "total_vectors": len(all_ids),
    }
    print(f"[INGEST] Done: {summary}")
    return summary


if __name__ == "__main__":
    ingest_all(reset=True)
