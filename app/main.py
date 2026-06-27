"""
FastAPI application entrypoint.

Run locally:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Then open:
    http://localhost:8000/docs   — interactive Swagger UI to test all endpoints
    http://localhost:8000/health — quick status check
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

# Allow the React frontend (localhost:3000) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="")


@app.on_event("startup")
async def startup_event():
    """
    On startup, pre-load the classifier model so the first request
    doesn't have a slow cold-start (DistilBERT takes a few seconds
    to load from disk).
    """
    print("[Startup] Pre-loading DistilBERT classifier...")
    try:
        from models.classifier_model import get_classifier
        get_classifier()
        print("[Startup] Classifier ready.")
    except Exception as e:
        print(f"[Startup WARNING] Classifier failed to load: {e}")
        print("  Check that models/trained_model_v2/ exists and contains model files.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=API_HOST, port=API_PORT, reload=True)
