"""
FastAPI routes: all API endpoints for the Ticket Resolution System.

Endpoints:
    GET  /health          — system status check
    POST /ingest          — (re)build the vector store from tickets + docs
    POST /query           — main RAG pipeline: classify → retrieve → generate
    POST /summarize       — summarize a long ticket description
"""

from fastapi import APIRouter, HTTPException

from app.config import TOP_K_RESULTS
from app.schemas import (
    QueryRequest,
    QueryResponse,
    SourceItem,
    SummarizeRequest,
    SummarizeResponse,
    IngestResponse,
    HealthResponse,
)
from models.classifier_model import get_classifier
from rag.ingestion import ingest_all
from rag.query_optimizer import rewrite_query
from rag.retriever import retrieve_similar, hybrid_retrieve
from rag.answer_generator import generate_answer, summarize_ticket

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    """
    Returns system status, the LLM provider in use, and how many
    vectors are currently in the store. Useful to confirm the server
    is running and the vector store has been populated before querying.
    """
    try:
        import chromadb
        from app.config import CHROMA_PERSIST_DIR, COLLECTION_NAME, LLM_PROVIDER
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        collection = client.get_or_create_collection(COLLECTION_NAME)
        vector_count = collection.count()
    except Exception:
        vector_count = -1

    from app.config import LLM_PROVIDER
    return HealthResponse(
        status="ok",
        llm_provider=LLM_PROVIDER,
        vector_count=vector_count,
    )


@router.post("/ingest", response_model=IngestResponse)
def ingest_knowledge_base():
    """
    (Re)build the vector store from tickets.csv and all documents in
    data/documents/ and data/manuals/. Safe to call multiple times —
    existing vectors are wiped and rebuilt cleanly each time.

    Call this once before querying, and again whenever you add new
    tickets or documents to the data folders.
    """
    try:
        result = ingest_all(reset=True)
        return IngestResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")


@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    """
    Main RAG pipeline:
    1. Classify the ticket using the fine-tuned DistilBERT classifier
    2. Rewrite the query for better retrieval
    3. Retrieve similar historical tickets + documents (vector or hybrid)
    4. Generate a grounded resolution using the LLM
    5. Return answer + confidence score + sources

    Set use_hybrid_search=true in the request body to enable BM25+vector
    hybrid retrieval (requires rank_bm25 installed).
    """
    try:
        # Step 1: Classify with the fine-tuned DistilBERT
        classifier = get_classifier()
        classification = classifier.classify(request.query)

        # Step 2: Rewrite query for better semantic retrieval
        rewritten = rewrite_query(request.query)

        # Step 3: Retrieve similar tickets/docs
        top_k = request.top_k or TOP_K_RESULTS
        if request.use_hybrid_search:
            retrieved = hybrid_retrieve(rewritten, top_k=top_k)
        else:
            retrieved = retrieve_similar(rewritten, top_k=top_k)

        # Step 4: Generate answer from retrieved context
        result = generate_answer(request.query, retrieved)

        return QueryResponse(
            original_query=request.query,
            rewritten_query=rewritten,
            category=classification["category"],
            category_confidence=classification["confidence"],
            answer=result["answer"],
            confidence=result["confidence"],
            confidence_label=result["confidence_label"],
            sources=[SourceItem(**s) for s in result["sources"]],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize", response_model=SummarizeResponse)
def summarize(request: SummarizeRequest):
    """
    Summarize a long incident report or ticket description into 2-3
    concise sentences while preserving key technical details.
    """
    try:
        summary = summarize_ticket(request.text)
        return SummarizeResponse(summary=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
