"""Tests for DeepFetch AI pipeline components."""

import pytest
from models.schemas import (
    PipelineState,
    QueryIntent,
    DocumentChunk,
    RetrievedChunk,
    Citation,
    ConfidenceLevel,
)


# ── Unit Tests: Chunking ─────────────────────────────────────────────────

class TestChunking:
    def test_chunk_short_text(self):
        from agents.ingestion import chunk_text

        text = "This is a short document."
        chunks = chunk_text(text, chunk_size=512)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_splits_long_text(self):
        from agents.ingestion import chunk_text

        # Create text longer than chunk_size
        paragraphs = [f"Paragraph {i}. " * 20 for i in range(10)]
        text = "\n\n".join(paragraphs)
        chunks = chunk_text(text, chunk_size=200, overlap=20)
        assert len(chunks) > 1

    def test_chunk_empty_text(self):
        from agents.ingestion import chunk_text

        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_chunk_preserves_content(self):
        from agents.ingestion import chunk_text

        text = "Hello world.\n\nThis is a test.\n\nThird paragraph."
        chunks = chunk_text(text, chunk_size=5000)
        # All content should be present in chunks
        joined = " ".join(chunks)
        assert "Hello world" in joined
        assert "This is a test" in joined
        assert "Third paragraph" in joined


# ── Unit Tests: Schema Validation ────────────────────────────────────────

class TestSchemas:
    def test_pipeline_state_defaults(self):
        state = PipelineState(original_query="test question")
        assert state.original_query == "test question"
        assert state.intent is None
        assert state.retrieved_chunks == []
        assert state.citations == []
        assert state.error is None

    def test_document_chunk_creation(self):
        chunk = DocumentChunk(
            chunk_id="abc123",
            document_name="test.pdf",
            content="Some content here",
            page_number=1,
            chunk_index=0,
        )
        assert chunk.chunk_id == "abc123"
        assert chunk.metadata == {}

    def test_query_intent_enum(self):
        assert QueryIntent.FACTUAL.value == "factual"
        assert QueryIntent.PROCEDURAL.value == "procedural"

    def test_confidence_level_enum(self):
        assert ConfidenceLevel.HIGH.value == "high"

    def test_citation_model(self):
        citation = Citation(
            citation_id=1,
            source_document="handbook.pdf",
            page_number=5,
            chunk_id="abc123",
            quoted_text="The policy states...",
        )
        assert citation.citation_id == 1


# ── Unit Tests: Rule-Based Validation ────────────────────────────────────

class TestValidationRules:
    def test_empty_answer_flagged(self):
        from agents.validation import _rule_based_checks

        state = PipelineState(
            original_query="test",
            answer="",
            retrieved_chunks=[
                RetrievedChunk(
                    chunk_id="a",
                    document_name="test.pdf",
                    content="content",
                    similarity_score=0.9,
                )
            ],
        )
        flags = _rule_based_checks(state)
        assert any("empty" in f.lower() or "short" in f.lower() for f in flags)

    def test_no_citations_flagged(self):
        from agents.validation import _rule_based_checks

        state = PipelineState(
            original_query="test",
            answer="This is a valid answer with enough text.",
            citations=[],
            retrieved_chunks=[
                RetrievedChunk(
                    chunk_id="a",
                    document_name="test.pdf",
                    content="content",
                    similarity_score=0.9,
                )
            ],
        )
        flags = _rule_based_checks(state)
        assert any("citation" in f.lower() for f in flags)

    def test_mismatched_citation_flagged(self):
        from agents.validation import _rule_based_checks

        state = PipelineState(
            original_query="test",
            answer="This is a valid answer with enough text.",
            citations=[
                Citation(
                    citation_id=1,
                    source_document="test.pdf",
                    chunk_id="nonexistent",
                    quoted_text="something",
                )
            ],
            retrieved_chunks=[
                RetrievedChunk(
                    chunk_id="actual_chunk",
                    document_name="test.pdf",
                    content="content",
                    similarity_score=0.9,
                )
            ],
        )
        flags = _rule_based_checks(state)
        assert any("nonexistent" in f for f in flags)

    def test_low_similarity_flagged(self):
        from agents.validation import _rule_based_checks

        state = PipelineState(
            original_query="test",
            answer="This is a valid answer with enough text.",
            citations=[],
            retrieved_chunks=[
                RetrievedChunk(
                    chunk_id="a",
                    document_name="test.pdf",
                    content="content",
                    similarity_score=0.1,  # Very low
                )
            ],
        )
        flags = _rule_based_checks(state)
        assert any("low retrieval" in f.lower() for f in flags)


# ── Integration Test Placeholder ─────────────────────────────────────────

class TestPipelineIntegration:
    """Integration tests require AWS credentials.
    
    Run with: pytest tests/ -m integration
    """

    @pytest.mark.integration
    def test_full_pipeline(self):
        """End-to-end test — requires Bedrock access and ingested docs."""
        from orchestrator.graph import run_query

        result = run_query("What is the company's PTO policy?")
        assert result.answer is not None
        assert result.confidence_score is not None
        assert result.latency_ms > 0
