"""Agent 3: Retrieval — multi-query FAISS search with reciprocal rank fusion."""

import logging
from collections import defaultdict

from config import config
from models.schemas import PipelineState, RetrievedChunk
from utils.bedrock_client import get_bedrock_client
from vectorstore.faiss_store import get_faiss_store

logger = logging.getLogger(__name__)

# Reciprocal Rank Fusion constant (standard value from literature)
RRF_K = 60


def run_retrieval(state: PipelineState) -> PipelineState:
    """Retrieve relevant chunks using multi-query search + RRF reranking."""
    bedrock = get_bedrock_client()
    store = get_faiss_store()

    if store.size == 0:
        logger.warning("FAISS index is empty — no documents ingested")
        state.retrieved_chunks = []
        state.error = "No documents have been ingested yet."
        return state

    top_k = config.MAX_CHUNKS_PER_QUERY
    search_queries = state.search_queries or [state.original_query]

    # ── Multi-query search ───────────────────────────────────────────────
    # Run each search query independently, then fuse results with RRF
    all_ranked_lists: list[list[RetrievedChunk]] = []

    for query in search_queries:
        query_embedding = bedrock.get_embedding(query)
        results = store.search(query_embedding, top_k=top_k * 2)  # oversample
        all_ranked_lists.append(results)

    # ── Reciprocal Rank Fusion ───────────────────────────────────────────
    # Combines rankings from multiple queries into a single ranking
    # Score = sum(1 / (k + rank)) across all ranked lists
    rrf_scores: dict[str, float] = defaultdict(float)
    chunk_map: dict[str, RetrievedChunk] = {}

    for ranked_list in all_ranked_lists:
        for rank, chunk in enumerate(ranked_list):
            rrf_scores[chunk.chunk_id] += 1.0 / (RRF_K + rank + 1)
            # Keep the version with highest similarity score
            if (
                chunk.chunk_id not in chunk_map
                or chunk.similarity_score
                > chunk_map[chunk.chunk_id].similarity_score
            ):
                chunk_map[chunk.chunk_id] = chunk

    # Sort by RRF score descending
    sorted_ids = sorted(rrf_scores, key=lambda cid: rrf_scores[cid], reverse=True)

    # Take top_k and attach rerank scores
    fused_results = []
    for chunk_id in sorted_ids[:top_k]:
        chunk = chunk_map[chunk_id]
        chunk.rerank_score = rrf_scores[chunk_id]
        fused_results.append(chunk)

    state.retrieved_chunks = fused_results

    logger.info(
        f"Retrieved {len(fused_results)} chunks "
        f"(from {len(search_queries)} queries, "
        f"RRF fusion over {sum(len(r) for r in all_ranked_lists)} candidates)"
    )

    # Log top result for debugging
    if fused_results:
        top = fused_results[0]
        logger.debug(
            f"Top chunk: {top.document_name} p.{top.page_number} "
            f"(sim={top.similarity_score:.3f}, rrf={top.rerank_score:.4f})"
        )

    return state
