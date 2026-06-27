"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, description="The user's IT issue description")
    top_k: Optional[int] = Field(None, description="Override number of results to retrieve")
    use_hybrid_search: bool = Field(False, description="Use BM25 + vector hybrid search")


class SourceItem(BaseModel):
    source: str
    source_type: str
    similarity: float


class QueryResponse(BaseModel):
    original_query: str
    rewritten_query: str
    category: str
    category_confidence: float
    answer: str
    confidence: float
    confidence_label: str
    sources: list[SourceItem]


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=10)


class SummarizeResponse(BaseModel):
    summary: str


class IngestResponse(BaseModel):
    tickets_ingested: int
    document_chunks_ingested: int
    total_vectors: int


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    vector_count: int
