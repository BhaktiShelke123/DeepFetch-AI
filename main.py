"""DeepFetch AI — FastAPI Application.

Endpoints:
    POST /ingest    — Ingest documents from the data/ directory
    POST /query     — Ask a question, get a cited answer
    GET  /documents — List ingested documents
    GET  /health    — Health check
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import config
from agents.ingestion import ingest_directory
from models.schemas import (
    HealthResponse,
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
)
from orchestrator.graph import run_query
from vectorstore.faiss_store import get_faiss_store

# ── Logging ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s │ %(name)-30s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan (load FAISS index on startup) ───────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting DeepFetch AI...")
    store = get_faiss_store()
    logger.info(f"FAISS index loaded: {store.size} vectors, {len(store.document_names)} documents")
    yield
    logger.info("Shutting down DeepFetch AI")


# ── App ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="DeepFetch AI",
    description="Multi-agent document intelligence engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Endpoints ────────────────────────────────────────────────────────────

@app.post("/ingest", response_model=IngestResponse)
def ingest_documents(request: IngestRequest = IngestRequest()):
    """Ingest all documents from the data/ directory (or a custom path)."""
    directory = request.directory or config.DATA_DIR
    try:
        results = ingest_directory(directory)
        total_chunks = sum(d.total_chunks for d in results)
        return IngestResponse(
            documents_processed=len(results),
            total_chunks=total_chunks,
            documents=results,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/query", response_model=QueryResponse)
def query_documents(request: QueryRequest):
    """Ask a question and get a cited answer from ingested documents."""
    store = get_faiss_store()
    if store.size == 0:
        raise HTTPException(
            status_code=400,
            detail="No documents ingested. Call POST /ingest first.",
        )

    try:
        result = run_query(request.question)

        return QueryResponse(
            answer=result.answer or "No answer generated.",
            citations=result.citations,
            confidence_score=result.confidence_score or 0.0,
            confidence_level=result.confidence_level,
            intent=result.intent,
            hallucination_flags=result.hallucination_flags,
            latency_ms=result.latency_ms or 0.0,
        )

    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/documents")
def list_documents():
    """List all ingested documents."""
    store = get_faiss_store()
    return {
        "documents": store.document_names,
        "total_chunks": store.size,
    }


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    store = get_faiss_store()
    return HealthResponse(
        status="healthy",
        documents_loaded=len(store.document_names),
        index_size=store.size,
    )


# ── Run ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
    )
