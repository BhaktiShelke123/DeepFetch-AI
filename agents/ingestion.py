"""Agent 1: Ingestion — Load documents, chunk text, embed, store in FAISS."""

import hashlib
import logging
from datetime import datetime, timezone

from config import config
from models.schemas import DocumentChunk, DocumentMetadata
from utils.bedrock_client import get_bedrock_client
from utils.document_loader import load_document, load_directory
from vectorstore.faiss_store import get_faiss_store

logger = logging.getLogger(__name__)


def chunk_text(
    text: str,
    chunk_size: int = config.CHUNK_SIZE,
    overlap: int = config.CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks by token-approximate character count.

    Uses a simple sentence-aware splitter:
    1. Split on double newlines (paragraphs) first
    2. If a paragraph exceeds chunk_size, split on sentences
    3. Merge small chunks up to chunk_size with overlap
    """
    if not text.strip():
        return []

    # Split into paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    # Break large paragraphs into sentences
    segments = []
    for para in paragraphs:
        if len(para) <= chunk_size:
            segments.append(para)
        else:
            # Split on sentence boundaries
            sentences = _split_sentences(para)
            segments.extend(sentences)

    # Merge segments into chunks with overlap
    chunks = []
    current_chunk = ""

    for segment in segments:
        candidate = (
            f"{current_chunk}\n\n{segment}" if current_chunk else segment
        )

        if len(candidate) <= chunk_size:
            current_chunk = candidate
        else:
            if current_chunk:
                chunks.append(current_chunk)
                # Overlap: keep the tail of the previous chunk
                overlap_text = current_chunk[-overlap:] if overlap > 0 else ""
                current_chunk = f"{overlap_text}\n\n{segment}".strip()
            else:
                # Single segment exceeds chunk_size — force add it
                chunks.append(segment[:chunk_size])
                current_chunk = segment[chunk_size - overlap:]

    if current_chunk.strip():
        chunks.append(current_chunk)

    return chunks


def _split_sentences(text: str) -> list[str]:
    """Basic sentence splitter."""
    import re

    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def _make_chunk_id(document_name: str, chunk_index: int) -> str:
    """Deterministic chunk ID so re-ingesting is idempotent."""
    raw = f"{document_name}::{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _assign_page_numbers(
    chunks: list[str], pages: list[str] | None
) -> list[int | None]:
    """Map each chunk to its source page number (best effort)."""
    if not pages:
        return [None] * len(chunks)

    # Build cumulative character offsets per page
    page_offsets = []
    offset = 0
    for page_text in pages:
        page_offsets.append(offset)
        offset += len(page_text) + 2  # +2 for the \n\n join

    # For each chunk, find which page it most likely came from
    full_text = "\n\n".join(pages)
    result = []
    for chunk in chunks:
        pos = full_text.find(chunk[:80])  # match on first 80 chars
        if pos == -1:
            result.append(None)
            continue
        # Find the page this position falls in
        page_num = 1
        for i, page_offset in enumerate(page_offsets):
            if pos >= page_offset:
                page_num = i + 1
        result.append(page_num)

    return result


def ingest_file(file_path: str) -> DocumentMetadata:
    """Ingest a single file: load → chunk → embed → store."""
    bedrock = get_bedrock_client()
    store = get_faiss_store()

    # 1. Load document
    doc = load_document(file_path)
    logger.info(f"Loaded {doc['filename']} ({len(doc['text'])} chars)")

    # 2. Chunk
    chunks_text = chunk_text(doc["text"])
    page_numbers = _assign_page_numbers(chunks_text, doc.get("pages"))
    logger.info(f"Created {len(chunks_text)} chunks")

    # 3. Build DocumentChunk objects
    doc_chunks = []
    for i, (text, page_num) in enumerate(zip(chunks_text, page_numbers)):
        doc_chunks.append(
            DocumentChunk(
                chunk_id=_make_chunk_id(doc["filename"], i),
                document_name=doc["filename"],
                content=text,
                page_number=page_num,
                chunk_index=i,
                metadata={
                    "file_type": doc["file_type"],
                    "char_count": len(text),
                },
            )
        )

    # 4. Embed
    logger.info("Generating embeddings via Bedrock Titan...")
    embeddings = bedrock.get_embeddings_batch(
        [c.content for c in doc_chunks]
    )

    # 5. Store in FAISS
    store.add(doc_chunks, embeddings)
    store.save()

    return DocumentMetadata(
        filename=doc["filename"],
        file_type=doc["file_type"],
        total_pages=doc.get("total_pages"),
        total_chunks=len(doc_chunks),
        ingested_at=datetime.now(timezone.utc).isoformat(),
    )


def ingest_directory(directory: str = config.DATA_DIR) -> list[DocumentMetadata]:
    """Ingest all supported files from a directory."""
    docs = load_directory(directory)

    if not docs:
        logger.warning(f"No supported documents found in {directory}")
        return []

    bedrock = get_bedrock_client()
    store = get_faiss_store()
    results = []

    for doc in docs:
        # Chunk
        chunks_text = chunk_text(doc["text"])
        page_numbers = _assign_page_numbers(chunks_text, doc.get("pages"))

        doc_chunks = []
        for i, (text, page_num) in enumerate(zip(chunks_text, page_numbers)):
            doc_chunks.append(
                DocumentChunk(
                    chunk_id=_make_chunk_id(doc["filename"], i),
                    document_name=doc["filename"],
                    content=text,
                    page_number=page_num,
                    chunk_index=i,
                    metadata={
                        "file_type": doc["file_type"],
                        "char_count": len(text),
                    },
                )
            )

        # Embed
        logger.info(f"Embedding {len(doc_chunks)} chunks from {doc['filename']}...")
        embeddings = bedrock.get_embeddings_batch(
            [c.content for c in doc_chunks]
        )

        # Store
        store.add(doc_chunks, embeddings)

        results.append(
            DocumentMetadata(
                filename=doc["filename"],
                file_type=doc["file_type"],
                total_pages=doc.get("total_pages"),
                total_chunks=len(doc_chunks),
                ingested_at=datetime.now(timezone.utc).isoformat(),
            )
        )

    # Persist the full index once at the end
    store.save()
    logger.info(
        f"Ingestion complete: {len(results)} documents, "
        f"{store.size} total chunks indexed"
    )
    return results
