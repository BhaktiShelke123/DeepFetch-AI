"""Agent 4: Reasoning — generate a cited answer from retrieved chunks using Bedrock."""

import json
import logging
from typing import Optional

from models.schemas import Citation, PipelineState
from utils.bedrock_client import get_bedrock_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a document intelligence assistant. Your job is to answer the user's question using ONLY the provided source chunks.

Rules:
1. Answer ONLY from the provided chunks. If the chunks don't contain the answer, say "I could not find this information in the available documents."
2. Cite every claim using [1], [2], etc. corresponding to the chunk numbers.
3. Be precise and concise — no filler.
4. If chunks partially answer the question, answer what you can and note what's missing.

After your answer, output a JSON block with your citations in this exact format:
---CITATIONS---
[
  {"citation_id": 1, "chunk_id": "abc123", "quoted_text": "exact text from chunk that supports this claim"},
  ...
]
---END_CITATIONS---"""


def _build_context(state: PipelineState) -> str:
    """Format retrieved chunks into a numbered context block."""
    if not state.retrieved_chunks:
        return "No relevant chunks were retrieved."

    lines = []
    for i, chunk in enumerate(state.retrieved_chunks, 1):
        source_info = f"Source: {chunk.document_name}"
        if chunk.page_number:
            source_info += f", Page {chunk.page_number}"
        source_info += f" (chunk_id: {chunk.chunk_id})"

        lines.append(
            f"--- Chunk [{i}] ---\n"
            f"{source_info}\n"
            f"{chunk.content}\n"
        )

    return "\n".join(lines)


def _parse_citations(
    raw_response: str, state: PipelineState
) -> tuple[str, list[Citation]]:
    """Split the LLM response into answer text and structured citations."""
    citations = []

    # Split on citation delimiter
    if "---CITATIONS---" in raw_response:
        parts = raw_response.split("---CITATIONS---")
        answer_text = parts[0].strip()

        if len(parts) > 1:
            citation_block = parts[1].split("---END_CITATIONS---")[0].strip()
            try:
                raw_citations = json.loads(citation_block)
                # Build a lookup for chunk metadata
                chunk_lookup = {
                    c.chunk_id: c for c in state.retrieved_chunks
                }

                for rc in raw_citations:
                    chunk_id = rc.get("chunk_id", "")
                    chunk = chunk_lookup.get(chunk_id)

                    citations.append(
                        Citation(
                            citation_id=rc.get("citation_id", 0),
                            source_document=(
                                chunk.document_name if chunk else "unknown"
                            ),
                            page_number=(
                                chunk.page_number if chunk else None
                            ),
                            chunk_id=chunk_id,
                            quoted_text=rc.get("quoted_text", ""),
                        )
                    )
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse citations JSON: {e}")
    else:
        answer_text = raw_response.strip()

    return answer_text, citations


def run_reasoning(state: PipelineState) -> PipelineState:
    """Generate an answer with citations from retrieved chunks."""
    bedrock = get_bedrock_client()

    if not state.retrieved_chunks:
        state.answer = (
            "I could not find relevant information in the available documents. "
            "Please try rephrasing your question or ingesting additional documents."
        )
        state.citations = []
        return state

    context = _build_context(state)

    prompt = (
        f"Context chunks:\n\n{context}\n\n"
        f"User question: {state.reformulated_query or state.original_query}\n\n"
        f"Answer the question using the chunks above. "
        f"Cite each claim with [chunk_number]. "
        f"Then output your citations in the JSON format specified."
    )

    try:
        raw_response = bedrock.invoke_llm(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            max_tokens=2048,
            temperature=0.2,
        )

        answer, citations = _parse_citations(raw_response, state)
        state.answer = answer
        state.citations = citations

        logger.info(
            f"Reasoning complete — "
            f"{len(answer)} char answer, {len(citations)} citations"
        )

    except Exception as e:
        logger.error(f"Reasoning failed: {e}")
        state.answer = "An error occurred while generating the answer."
        state.citations = []
        state.error = f"Reasoning error: {str(e)}"

    return state
