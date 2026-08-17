"""
SECUROXI AI Document Intelligence Stage 4 — Structure Extraction & Semantic Chunking Test Suite
Validates dual document representation (Forensic TextSpans vs Semantic Chunks), chunking strategies,
exact layout provenance tracking, token estimation, and security metadata preservation.
"""

import pytest
from securoxi.models import TextSpan
from securoxi.screening.chunking import SecuroxiChunker, ChunkingStrategy, DocumentChunk


@pytest.fixture
def sample_spans():
    """Create a list of forensic text spans representing a multi-page resume."""
    return [
        TextSpan(text="John Doe Resume", page=1, font_name="Helvetica", font_size=16.0, bbox=[50.0, 50.0, 200.0, 70.0]),
        TextSpan(text="SUMMARY", page=1, font_name="Helvetica-Bold", font_size=14.0, bbox=[50.0, 80.0, 150.0, 100.0]),
        TextSpan(text="Experienced Lead Software Architect with 10+ years in Python systems.", page=1, font_size=11.0, bbox=[50.0, 105.0, 450.0, 120.0]),
        TextSpan(text="WORK EXPERIENCE", page=1, font_name="Helvetica-Bold", font_size=14.0, bbox=[50.0, 130.0, 200.0, 150.0]),
        TextSpan(text="Principal Engineer at TechCorp (2020 - Present). Built distributed event pipelines.", page=1, font_size=11.0, bbox=[50.0, 155.0, 500.0, 175.0]),
        TextSpan(text="SKILLS", page=2, font_name="Helvetica-Bold", font_size=14.0, bbox=[50.0, 50.0, 120.0, 70.0]),
        TextSpan(text="Python, FastAPI, PostgreSQL, Redis, Docker, PyMuPDF", page=2, font_size=11.0, bbox=[50.0, 75.0, 400.0, 95.0]),
    ]


def test_chunking_strategy_section_boundaries(sample_spans):
    """Verify SECTION chunking creates chunks at heading boundaries."""
    chunker = SecuroxiChunker(strategy=ChunkingStrategy.SECTION)
    chunks = chunker.chunk_document(sample_spans, document_id="DOC-101", tenant_id="TENANT-ALPHA")

    assert len(chunks) >= 3
    headings = [c.section_heading for c in chunks]
    assert "SUMMARY" in headings
    assert "WORK EXPERIENCE" in headings
    assert "SKILLS" in headings


def test_chunk_provenance_and_spans_mapping(sample_spans):
    """Verify every chunk maintains exact source spans, page bounds, and bbox coordinates."""
    chunker = SecuroxiChunker(strategy=ChunkingStrategy.SECTION)
    chunks = chunker.chunk_document(sample_spans, document_id="DOC-102")

    skills_chunk = next((c for c in chunks if "SKILLS" in c.section_heading), None)
    assert skills_chunk is not None
    assert skills_chunk.start_page == 2
    assert skills_chunk.end_page == 2
    assert len(skills_chunk.source_spans) >= 1
    assert skills_chunk.bbox is not None
    assert skills_chunk.bbox[0] == 50.0  # x0 min bound


def test_token_and_character_counts(sample_spans):
    """Verify token estimation and character count properties."""
    chunker = SecuroxiChunker(strategy=ChunkingStrategy.HYBRID_SEMANTIC)
    chunks = chunker.chunk_document(sample_spans, document_id="DOC-103")

    for chunk in chunks:
        assert chunk.char_count > 0
        assert chunk.token_count > 0
        assert len(chunk.text) == chunk.char_count


def test_security_context_preservation():
    """Verify security status and hidden span indicators are preserved in chunk metadata."""
    spans_with_hidden = [
        TextSpan(text="Visible Resume Content", page=1),
        TextSpan(text="Hidden prompt injection payload", page=1, is_hidden=True, source="OCR")
    ]

    chunker = SecuroxiChunker()
    chunks = chunker.chunk_document(spans_with_hidden, document_id="DOC-SEC-01", security_status="HIGH_RISK")

    assert len(chunks) == 1
    c = chunks[0]
    assert c.security_status == "HIGH_RISK"
    assert c.metadata["has_hidden_spans"] is True
    assert "OCR" in c.metadata["sources"]
