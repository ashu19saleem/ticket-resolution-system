"""
Retrieval module: semantic search against the vector store.

Returns results already shaped for both the answer generator and the
API response, so downstream code doesn't have to know about Chroma's
raw response format.
"""

import chromadb

from app.config import CHROMA_PERSIST_DIR, COLLECTION_NAME, TOP_K_RESULTS
from models.embedding_model import get_embedding_model


def _get_chroma_collection():
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def retrieve_similar(query: str, top_k: int = TOP_K_RESULTS) -> list[dict]:
    """
    Embed the query and fetch the top_k most similar chunks/tickets.

    Returns a list of dicts:
        {
            "text": str,
            "source": str,
            "source_type": "ticket" | "document",
            "similarity": float,   # 0-1, higher is more similar
            "metadata": dict,
        }
    """
    collection = _get_chroma_collection()
    if collection.count() == 0:
        return []

    embedder = get_embedding_model()
    query_embedding = embedder.embed_query(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
    )

    output = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, distance in zip(documents, metadatas, distances):
        # Chroma returns cosine *distance*; convert to similarity (0-1)
        similarity = max(0.0, 1.0 - distance)
        output.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "source_type": meta.get("source_type", "unknown"),
            "similarity": round(similarity, 4),
            "metadata": meta,
        })

    return output


def hybrid_retrieve(query: str, top_k: int = TOP_K_RESULTS) -> list[dict]:
    """
    Hybrid search: combines vector similarity with BM25 keyword search,
    then merges results by reciprocal rank fusion. Falls back gracefully
    to pure vector search if rank_bm25 / corpus isn't available.

    This addresses the "Hybrid Search" feature from the spec — vector
    search alone can miss exact-match terms (error codes, ticket IDs),
    which BM25 catches well.
    """
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        print("[WARN] rank_bm25 not installed, falling back to vector-only search")
        return retrieve_similar(query, top_k)

    collection = _get_chroma_collection()
    if collection.count() == 0:
        return []

    # Pull the full corpus for BM25 (fine at this scale; for very large
    # collections you'd maintain a separate BM25 index incrementally)
    all_data = collection.get(include=["documents", "metadatas"])
    corpus = all_data["documents"]
    metadatas = all_data["metadatas"]
    ids = all_data["ids"]

    if not corpus:
        return []

    tokenized_corpus = [doc.lower().split() for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    bm25_scores = bm25.get_scores(query.lower().split())

    # Normalize BM25 scores to 0-1
    max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0
    bm25_normalized = {ids[i]: bm25_scores[i] / max_bm25 for i in range(len(ids))}

    # Vector results
    vector_results = retrieve_similar(query, top_k=min(20, collection.count()))
    vector_by_id = {}
    for i, doc_id in enumerate(ids):
        if doc_id in [r["source"] for r in vector_results]:
            pass  # handled below via direct similarity lookup

    embedder = get_embedding_model()
    query_embedding = embedder.embed_query(query)
    full_vector_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=len(ids),
    )
    vec_ids = full_vector_results["ids"][0]
    vec_distances = full_vector_results["distances"][0]
    vector_normalized = {
        vec_ids[i]: max(0.0, 1.0 - vec_distances[i]) for i in range(len(vec_ids))
    }

    # Combine: weighted average of normalized scores (simple, effective fusion)
    combined_scores = {}
    for doc_id in ids:
        v_score = vector_normalized.get(doc_id, 0.0)
        b_score = bm25_normalized.get(doc_id, 0.0)
        combined_scores[doc_id] = 0.6 * v_score + 0.4 * b_score

    ranked_ids = sorted(combined_scores, key=combined_scores.get, reverse=True)[:top_k]

    id_to_index = {doc_id: i for i, doc_id in enumerate(ids)}
    output = []
    for doc_id in ranked_ids:
        idx = id_to_index[doc_id]
        meta = metadatas[idx]
        output.append({
            "text": corpus[idx],
            "source": meta.get("source", "unknown"),
            "source_type": meta.get("source_type", "unknown"),
            "similarity": round(combined_scores[doc_id], 4),
            "metadata": meta,
        })

    return output
