"""
FastAPI application entrypoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS, API_HOST, API_PORT
from app.routes import router

app = FastAPI(
    title="Intelligent Ticket Resolution System",
    description=(
        "AI-powered IT support ticket resolution using RAG + LLM. "
        "Retrieves similar historical tickets and documents, then generates "
        "a grounded step-by-step resolution with a confidence score."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="")


@app.on_event("startup")
async def startup_event():
    """Pre-load classifier and auto-ingest tickets on startup."""

    print("[Startup] Pre-loading classifier...")
    try:
        from models.classifier_model import get_classifier
        get_classifier()
        print("[Startup] Classifier ready.")
    except Exception as e:
        print(f"[Startup WARNING] Classifier failed to load: {e}")

    print("[Startup] Auto-ingesting tickets into vector store...")
    try:
        import chromadb
        from app.config import CHROMA_PERSIST_DIR, COLLECTION_NAME
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        collection = client.get_or_create_collection(COLLECTION_NAME)
        count = collection.count()

        if count == 0:
            print("[Startup] Vector store empty — running ingestion...")
            from rag.ingestion import ingest_all
            result = ingest_all(reset=False)
            print(f"[Startup] Ingestion complete: {result}")
        else:
            print(f"[Startup] Vector store already has {count} vectors — skipping ingestion.")
    except Exception as e:
        print(f"[Startup WARNING] Auto-ingestion failed: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=API_HOST, port=API_PORT, reload=True)