"""FAISS vector store wrapper with persistence and metadata tracking."""

import json
import logging
import os
from pathlib import Path
from typing import Optional

import faiss
import numpy as np

from config import config
from models.schemas import DocumentChunk, RetrievedChunk

logger = logging.getLogger(__name__)


class FAISSStore:
    """FAISS index wrapper that stores embeddings + chunk metadata together."""

    def __init__(self, index_path: Optional[str] = None):
        self.index_path = index_path or config.FAISS_INDEX_PATH
        self.dimension = config.EMBEDDING_DIMENSION
        self.index: Optional[faiss.IndexFlatIP] = None  # Inner product (cosine sim on normalized vecs)
        self.chunks: list[DocumentChunk] = []  # Parallel array — chunks[i] matches index row i
        self._load_or_create()

    def _load_or_create(self):
        """Load existing index from disk, or create a new empty one."""
        index_file = f"{self.index_path}.faiss"
        meta_file = f"{self.index_path}.meta.json"

        if os.path.exists(index_file) and os.path.exists(meta_file):
            logger.info(f"Loading existing FAISS index from {index_file}")
            self.index = faiss.read_index(index_file)

            with open(meta_file, "r") as f:
                raw_chunks = json.load(f)
            self.chunks = [DocumentChunk(**c) for c in raw_chunks]

            logger.info(
                f"Loaded index with {self.index.ntotal} vectors, "
                f"{len(self.chunks)} chunks"
            )
        else:
            logger.info("Creating new FAISS index")
            self.index = faiss.IndexFlatIP(self.dimension)
            self.chunks = []

    def add(self, chunks: list[DocumentChunk], embeddings: list[list[float]]):
        """Add chunks and their embeddings to the index."""
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Chunk count ({len(chunks)}) != embedding count ({len(embeddings)})"
            )

        # Normalize vectors for cosine similarity via inner product
        vectors = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(vectors)

        self.index.add(vectors)
        self.chunks.extend(chunks)

        logger.info(
            f"Added {len(chunks)} chunks. "
            f"Index now has {self.index.ntotal} vectors."
        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """Search the index and return top-k matching chunks with scores."""
        if self.index.ntotal == 0:
            logger.warning("Search called on empty index")
            return []

        # Normalize query vector
        query_vec = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_vec)

        # Search
        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            chunk = self.chunks[idx]
            results.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    document_name=chunk.document_name,
                    content=chunk.content,
                    page_number=chunk.page_number,
                    similarity_score=float(score),
                )
            )

        return results

    def save(self):
        """Persist index and metadata to disk."""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)

        index_file = f"{self.index_path}.faiss"
        meta_file = f"{self.index_path}.meta.json"

        faiss.write_index(self.index, index_file)

        with open(meta_file, "w") as f:
            json.dump([c.model_dump() for c in self.chunks], f)

        logger.info(
            f"Saved index ({self.index.ntotal} vectors) to {index_file}"
        )

    def clear(self):
        """Reset the index."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.chunks = []
        logger.info("Index cleared")

    @property
    def size(self) -> int:
        return self.index.ntotal if self.index else 0

    @property
    def document_names(self) -> list[str]:
        return list({c.document_name for c in self.chunks})


# Singleton
_store: Optional[FAISSStore] = None


def get_faiss_store() -> FAISSStore:
    global _store
    if _store is None:
        _store = FAISSStore()
    return _store
