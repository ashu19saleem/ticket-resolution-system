"""
Central configuration for the Ticket Resolution System.
All paths, model names, and tunable parameters live here so nothing
is hardcoded deep inside the pipeline.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---------- Paths ----------
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
TICKETS_CSV = DATA_DIR / "tickets.csv"
DOCUMENTS_DIR = DATA_DIR / "documents"
MANUALS_DIR = DATA_DIR / "manuals"

EMBEDDINGS_DIR = BASE_DIR / "embeddings"
CHROMA_PERSIST_DIR = str(EMBEDDINGS_DIR / "chroma_store")

# ---------- Embedding Model ----------
# Local, free, no API key required. Swap to "BAAI/bge-small-en-v1.5" if you
# want slightly higher retrieval quality at the cost of a larger download.
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

# ---------- Vector Store ----------
VECTOR_DB_PROVIDER = os.getenv("VECTOR_DB_PROVIDER", "chroma")  # chroma | faiss
COLLECTION_NAME = "ticket_resolution_kb"

# ---------- LLM ----------
# Supported providers: "groq" (default, free tier), "openai", "gemini"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ---------- Retrieval ----------
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", 5))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 800))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 120))

# ---------- Confidence Scoring ----------
# Minimum similarity (0-1) required before we consider a source "relevant"
MIN_RELEVANCE_THRESHOLD = float(os.getenv("MIN_RELEVANCE_THRESHOLD", 0.35))

# ---------- Ticket Categories (for classification) ----------
TICKET_CATEGORIES = [
    "Network Issue",
    "Login Problem",
    "Database Error",
    "Server Down",
    "Performance Issue",
    "Email Issue",
    "VPN Issue",
    "Other",
]

# ---------- API ----------
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
