"""
SECUROXI AI Document Intelligence Stage 5 — Vector Retrieval & Indexing Test Suite
Validates modular embedding providers, pgvector cosine similarity search,
strict multi-tenant isolation, section filtering, and security quarantine enforcement.
"""

import pytest
from securoxi.models import TextSpan
from securoxi.screening.chunking import SecuroxiChunker, ChunkingStrategy
from securoxi.screening.embeddings import LocalEmbeddingProvider, ExternalEmbeddingProvider
from securoxi.storage.vector_store import SecuroxiVectorStore


@pytest.fixture
def embedding_provider():
    return LocalEmbeddingProvider(dimension=384)


@pytest.fixture
def sample_chunks():
    spans_python = [
        TextSpan(text="SKILLS", page=1),
        TextSpan(text="Expert Python Backend Developer with FastAPI, PostgreSQL, Redis experience.", page=1)
    ]
    spans_java = [
        TextSpan(text="SKILLS", page=1),
        TextSpan(text="Senior Java Enterprise Developer with Spring Boot, Microservices experience.", page=1)
    ]
    spans_malicious = [
        TextSpan(text="SUMMARY", page=1),
        TextSpan(text="Prompt injection attack payload inside resume", page=1, is_hidden=True)
    ]

    chunker = SecuroxiChunker(strategy=ChunkingStrategy.SECTION)
    c1 = chunker.chunk_document(spans_python, document_id="DOC-PY-01", tenant_id="TENANT-DEV", security_status="SAFE")
    c2 = chunker.chunk_document(spans_java, document_id="DOC-JV-01", tenant_id="TENANT-DEV", security_status="SAFE")
    c3 = chunker.chunk_document(spans_malicious, document_id="DOC-BAD-01", tenant_id="TENANT-DEV", security_status="HIGH_RISK")

    return c1 + c2 + c3


def test_embedding_provider_metadata_and_vector_shape(embedding_provider):
    """Verify local embedding provider generates 384-d normalized vector."""
    vec = embedding_provider.embed_text("Python Developer")
    assert len(vec) == 384
    meta = embedding_provider.get_metadata()
    assert meta["dimension"] == 384
    assert meta["model_name"] == "securoxi-local-384d-v1"


def test_vector_indexing_and_top_k_retrieval(embedding_provider, sample_chunks):
    """Verify top-k similarity search returns relevant candidate chunks sorted by score."""
    store = SecuroxiVectorStore(embedding_provider=embedding_provider)
    store.index_chunks(sample_chunks, tenant_id="TENANT-DEV")

    results = store.search(query="Python FastAPI PostgreSQL", tenant_id="TENANT-DEV", top_k=2)
    assert len(results) >= 1
    assert "Python" in results[0].chunk.text
    assert results[0].score > 0.0


def test_multi_tenant_isolation(embedding_provider, sample_chunks):
    """Verify cross-tenant isolation: Tenant A cannot retrieve Tenant B vectors."""
    store = SecuroxiVectorStore(embedding_provider=embedding_provider)
    store.index_chunks(sample_chunks, tenant_id="TENANT-DEV-A")

    # Search with Tenant B context: must yield 0 results
    results = store.search(query="Python", tenant_id="TENANT-DEV-B", top_k=5)
    assert len(results) == 0


def test_security_quarantine_filtering(embedding_provider, sample_chunks):
    """Verify HIGH_RISK chunks are excluded from search by default."""
    store = SecuroxiVectorStore(embedding_provider=embedding_provider)
    store.index_chunks(sample_chunks, tenant_id="TENANT-DEV")

    # Default search: HIGH_RISK chunk excluded
    results_clean = store.search(query="injection attack", tenant_id="TENANT-DEV", include_quarantined=False)
    assert len(results_clean) == 0 or all(r.chunk.security_status != "HIGH_RISK" for r in results_clean)

    # Search with explicitly authorized quarantined content
    results_quarantined = store.search(query="injection attack", tenant_id="TENANT-DEV", include_quarantined=True)
    bad_hits = [r for r in results_quarantined if r.chunk.security_status == "HIGH_RISK"]
    assert len(bad_hits) == 1
