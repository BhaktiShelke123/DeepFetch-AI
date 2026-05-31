"""Agent 5: Validation — hallucination detection + confidence scoring."""

import json
import logging

from models.schemas import ConfidenceLevel, PipelineState
from utils.bedrock_client import get_bedrock_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a validation agent that checks answers for accuracy and hallucination.

You receive:
1. The original question
2. The source chunks that were retrieved
3. The generated answer with citations

Your job is to check:
- Does each cited claim actually appear in the source chunks?
- Does the answer contain any information NOT in the source chunks (hallucination)?
- How confident should we be in this answer?

Respond with ONLY valid JSON:
{
  "confidence_score": 0.0 to 1.0,
  "hallucination_flags": ["list of specific claims not supported by sources"],
  "is_valid": true/false,
  "reasoning": "brief explanation of your assessment"
}"""


def _build_validation_prompt(state: PipelineState) -> str:
    """Build the validation prompt from pipeline state."""
    chunks_text = ""
    for i, chunk in enumerate(state.retrieved_chunks, 1):
        chunks_text += (
            f"[Chunk {i}] ({chunk.document_name}, p.{chunk.page_number}):\n"
            f"{chunk.content}\n\n"
        )

    citations_text = ""
    for c in state.citations:
        citations_text += (
            f"  [{c.citation_id}] from {c.source_document}: "
            f'"{c.quoted_text}"\n'
        )

    return (
        f"QUESTION: {state.original_query}\n\n"
        f"SOURCE CHUNKS:\n{chunks_text}\n"
        f"GENERATED ANSWER:\n{state.answer}\n\n"
        f"CITATIONS:\n{citations_text}\n\n"
        f"Validate this answer. Return JSON only."
    )


def _rule_based_checks(state: PipelineState) -> list[str]:
    """Fast rule-based validation before calling the LLM."""
    flags = []

    # Check: answer exists
    if not state.answer or len(state.answer.strip()) < 10:
        flags.append("Answer is empty or too short")

    # Check: citations exist
    if not state.citations and state.retrieved_chunks:
        flags.append("No citations provided despite having source chunks")

    # Check: citation chunk_ids actually match retrieved chunks
    retrieved_ids = {c.chunk_id for c in state.retrieved_chunks}
    for citation in state.citations:
        if citation.chunk_id not in retrieved_ids:
            flags.append(
                f"Citation [{citation.citation_id}] references chunk "
                f"'{citation.chunk_id}' which was not in retrieved results"
            )

    # Check: retrieval quality
    if state.retrieved_chunks:
        top_score = state.retrieved_chunks[0].similarity_score
        if top_score < 0.3:
            flags.append(
                f"Low retrieval confidence — top similarity score: {top_score:.3f}"
            )

    return flags


def run_validation(state: PipelineState) -> PipelineState:
    """Validate the generated answer for hallucination and assign confidence."""
    # ── Step 1: Rule-based checks ────────────────────────────────────────
    rule_flags = _rule_based_checks(state)

    # If answer is clearly bad, skip the LLM call
    if not state.answer or not state.retrieved_chunks:
        state.confidence_score = 0.1
        state.confidence_level = ConfidenceLevel.LOW
        state.hallucination_flags = rule_flags or ["No answer or no source chunks"]
        state.is_valid = False
        return state

    # ── Step 2: LLM-based validation ─────────────────────────────────────
    bedrock = get_bedrock_client()

    try:
        prompt = _build_validation_prompt(state)
        raw_response = bedrock.invoke_llm(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            max_tokens=1024,
            temperature=0.1,
        )

        cleaned = raw_response.strip().strip("```json").strip("```").strip()
        parsed = json.loads(cleaned)

        llm_confidence = float(parsed.get("confidence_score", 0.5))
        llm_flags = parsed.get("hallucination_flags", [])
        llm_valid = parsed.get("is_valid", True)

        # Combine rule-based and LLM flags
        all_flags = rule_flags + llm_flags

        # Penalize confidence for rule-based flags
        penalty = len(rule_flags) * 0.1
        final_confidence = max(0.0, min(1.0, llm_confidence - penalty))

        state.confidence_score = round(final_confidence, 3)
        state.hallucination_flags = all_flags
        state.is_valid = llm_valid and len(rule_flags) == 0

    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Validation parse failed: {e}. Using rule-based only.")
        state.confidence_score = 0.5 if not rule_flags else 0.3
        state.hallucination_flags = rule_flags
        state.is_valid = len(rule_flags) == 0

    except Exception as e:
        logger.error(f"Validation LLM call failed: {e}")
        state.confidence_score = 0.4
        state.hallucination_flags = rule_flags + [f"Validation error: {str(e)}"]
        state.is_valid = len(rule_flags) == 0

    # ── Set confidence level ─────────────────────────────────────────────
    if state.confidence_score >= 0.8:
        state.confidence_level = ConfidenceLevel.HIGH
    elif state.confidence_score >= 0.5:
        state.confidence_level = ConfidenceLevel.MEDIUM
    else:
        state.confidence_level = ConfidenceLevel.LOW

    logger.info(
        f"Validation complete — confidence: {state.confidence_score} "
        f"({state.confidence_level.value}), "
        f"{len(state.hallucination_flags)} flags, "
        f"valid: {state.is_valid}"
    )

    return state
