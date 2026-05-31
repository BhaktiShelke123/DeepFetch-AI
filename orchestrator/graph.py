"""LangGraph orchestrator — state machine pipeline with error recovery.

Pipeline flow:
    query_understanding → retrieval → reasoning → validation → END

Each node receives and returns a PipelineState dict.
If any node sets state["error"], the pipeline routes to an error handler.
"""

import logging
import time
from typing import Any

from langgraph.graph import END, StateGraph

from models.schemas import ConfidenceLevel, PipelineState, QueryIntent

logger = logging.getLogger(__name__)


# ── State type for LangGraph (dict-based) ────────────────────────────────
# LangGraph works with dicts, so we convert PipelineState to/from dict
# at the graph boundaries.

GraphState = dict[str, Any]


def _to_dict(state: PipelineState) -> GraphState:
    return state.model_dump()


def _from_dict(data: GraphState) -> PipelineState:
    return PipelineState(**data)


# ── Node wrappers ────────────────────────────────────────────────────────

def query_understanding_node(state: GraphState) -> GraphState:
    """Node 1: Analyze and reformulate the query."""
    from agents.query_understanding import run_query_understanding

    pipeline_state = _from_dict(state)
    result = run_query_understanding(pipeline_state)
    return _to_dict(result)


def retrieval_node(state: GraphState) -> GraphState:
    """Node 2: Retrieve relevant chunks from FAISS."""
    from agents.retrieval import run_retrieval

    pipeline_state = _from_dict(state)
    result = run_retrieval(pipeline_state)
    return _to_dict(result)


def reasoning_node(state: GraphState) -> GraphState:
    """Node 3: Generate a cited answer."""
    from agents.reasoning import run_reasoning

    pipeline_state = _from_dict(state)
    result = run_reasoning(pipeline_state)
    return _to_dict(result)


def validation_node(state: GraphState) -> GraphState:
    """Node 4: Validate for hallucination and score confidence."""
    from agents.validation import run_validation

    pipeline_state = _from_dict(state)
    result = run_validation(pipeline_state)
    return _to_dict(result)


def error_handler_node(state: GraphState) -> GraphState:
    """Fallback node — returns a safe error response."""
    logger.error(f"Pipeline error: {state.get('error', 'Unknown error')}")
    state["answer"] = (
        "I encountered an error while processing your question. "
        "Please try again or rephrase your query."
    )
    state["confidence_score"] = 0.0
    state["confidence_level"] = ConfidenceLevel.LOW.value
    state["is_valid"] = False
    return state


# ── Routing logic ────────────────────────────────────────────────────────

def should_continue_after_understanding(state: GraphState) -> str:
    if state.get("error"):
        return "error_handler"
    return "retrieval"


def should_continue_after_retrieval(state: GraphState) -> str:
    if state.get("error"):
        return "error_handler"
    if not state.get("retrieved_chunks"):
        # No chunks found — skip reasoning, go straight to validation
        # which will assign low confidence
        return "reasoning"
    return "reasoning"


def should_continue_after_reasoning(state: GraphState) -> str:
    if state.get("error"):
        return "error_handler"
    return "validation"


# ── Build the graph ──────────────────────────────────────────────────────

def build_pipeline() -> StateGraph:
    """Construct and compile the LangGraph pipeline."""
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("query_understanding", query_understanding_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("error_handler", error_handler_node)

    # Set entry point
    workflow.set_entry_point("query_understanding")

    # Add conditional edges
    workflow.add_conditional_edges(
        "query_understanding",
        should_continue_after_understanding,
        {"retrieval": "retrieval", "error_handler": "error_handler"},
    )

    workflow.add_conditional_edges(
        "retrieval",
        should_continue_after_retrieval,
        {"reasoning": "reasoning", "error_handler": "error_handler"},
    )

    workflow.add_conditional_edges(
        "reasoning",
        should_continue_after_reasoning,
        {"validation": "validation", "error_handler": "error_handler"},
    )

    # Terminal edges
    workflow.add_edge("validation", END)
    workflow.add_edge("error_handler", END)

    return workflow.compile()


# ── Public interface ─────────────────────────────────────────────────────

_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = build_pipeline()
    return _pipeline


def run_query(question: str) -> PipelineState:
    """Run the full pipeline on a question. Returns the final PipelineState."""
    pipeline = get_pipeline()

    initial_state: GraphState = _to_dict(
        PipelineState(original_query=question)
    )

    start_time = time.time()
    final_state = pipeline.invoke(initial_state)
    elapsed_ms = (time.time() - start_time) * 1000

    final_state["latency_ms"] = round(elapsed_ms, 1)

    result = _from_dict(final_state)

    logger.info(
        f"Pipeline complete in {result.latency_ms}ms — "
        f"confidence: {result.confidence_score} ({result.confidence_level})"
    )

    return result
