from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────

class QueryIntent(str, Enum):
    FACTUAL = "factual"           # "What is the PTO policy?"
    PROCEDURAL = "procedural"     # "How do I submit an expense report?"
    COMPARATIVE = "comparative"   # "What's the difference between Plan A and Plan B?"
    EXPLORATORY = "exploratory"   # "Tell me about the onboarding process"


class ConfidenceLevel(str, Enum):
    HIGH = "high"       # >= 0.8
    MEDIUM = "medium"   # 0.5 - 0.8
    LOW = "low"         # < 0.5


# ── Document Models ──────────────────────────────────────────────────────

class DocumentChunk(BaseModel):
    chunk_id: str
    document_name: str
    content: str
    page_number: Optional[int] = None
    chunk_index: int
    metadata: dict = Field(default_factory=dict)


class DocumentMetadata(BaseModel):
    filename: str
    file_type: str
    total_pages: Optional[int] = None
    total_chunks: int
    ingested_at: str


# ── Pipeline State (used by LangGraph) ───────────────────────────────────

class PipelineState(BaseModel):
    """Full state passed through the LangGraph pipeline."""

    # Input
    original_query: str
    
    # Query Understanding output
    intent: Optional[QueryIntent] = None
    reformulated_query: Optional[str] = None
    search_queries: list[str] = Field(default_factory=list)

    # Retrieval output
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)

    # Reasoning output
    answer: Optional[str] = None
    citations: list[Citation] = Field(default_factory=list)

    # Validation output
    confidence_score: Optional[float] = None
    confidence_level: Optional[ConfidenceLevel] = None
    hallucination_flags: list[str] = Field(default_factory=list)
    is_valid: Optional[bool] = None

    # Metadata
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_name: str
    content: str
    page_number: Optional[int] = None
    similarity_score: float
    rerank_score: Optional[float] = None


class Citation(BaseModel):
    citation_id: int
    source_document: str
    page_number: Optional[int] = None
    chunk_id: str
    quoted_text: str


# ── API Request / Response ───────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confidence_score: float
    confidence_level: ConfidenceLevel
    intent: QueryIntent
    hallucination_flags: list[str]
    latency_ms: float


class IngestRequest(BaseModel):
    directory: Optional[str] = None  # defaults to config.DATA_DIR


class IngestResponse(BaseModel):
    documents_processed: int
    total_chunks: int
    documents: list[DocumentMetadata]


class HealthResponse(BaseModel):
    status: str
    documents_loaded: int
    index_size: int
