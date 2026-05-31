"""Agent 2: Query Understanding — classify intent and reformulate for better retrieval."""

import json
import logging

from models.schemas import PipelineState, QueryIntent
from utils.bedrock_client import get_bedrock_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a query analysis agent inside a document intelligence system.

Your job is to analyze the user's question and produce a JSON response with:
1. "intent" — one of: factual, procedural, comparative, exploratory
2. "reformulated_query" — a clearer version optimized for semantic search
3. "search_queries" — 1-3 alternative phrasings to maximize retrieval recall

Intent definitions:
- factual: asking for a specific fact ("What is the PTO policy?")
- procedural: asking how to do something ("How do I submit expenses?")
- comparative: comparing two or more things ("Difference between Plan A and Plan B?")
- exploratory: open-ended exploration ("Tell me about onboarding")

Respond with ONLY valid JSON, no markdown fences, no explanation."""

USER_TEMPLATE = """Analyze this question:

"{query}"

Return JSON with keys: intent, reformulated_query, search_queries"""


def run_query_understanding(state: PipelineState) -> PipelineState:
    """Analyze the user's query — classify intent and generate search queries."""
    bedrock = get_bedrock_client()

    prompt = USER_TEMPLATE.format(query=state.original_query)

    try:
        raw_response = bedrock.invoke_llm(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            max_tokens=512,
            temperature=0.1,
        )

        # Parse JSON response
        cleaned = raw_response.strip().strip("```json").strip("```").strip()
        parsed = json.loads(cleaned)

        # Map intent string to enum
        intent_str = parsed.get("intent", "factual").lower()
        try:
            state.intent = QueryIntent(intent_str)
        except ValueError:
            state.intent = QueryIntent.FACTUAL

        state.reformulated_query = parsed.get(
            "reformulated_query", state.original_query
        )
        state.search_queries = parsed.get(
            "search_queries", [state.original_query]
        )

        # Always include the original query as a search query
        if state.original_query not in state.search_queries:
            state.search_queries.insert(0, state.original_query)

        logger.info(
            f"Query understood — intent: {state.intent.value}, "
            f"{len(state.search_queries)} search queries generated"
        )

    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Query understanding parse failed: {e}. Using defaults.")
        state.intent = QueryIntent.FACTUAL
        state.reformulated_query = state.original_query
        state.search_queries = [state.original_query]

    except Exception as e:
        logger.error(f"Query understanding failed: {e}")
        state.intent = QueryIntent.FACTUAL
        state.reformulated_query = state.original_query
        state.search_queries = [state.original_query]
        state.error = f"Query understanding error: {str(e)}"

    return state
