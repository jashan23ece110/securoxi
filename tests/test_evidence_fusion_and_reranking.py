"""
SECUROXI AI Intelligence 2.0 — Evidence Fusion & Advanced Reranking Test Suite
Validates hybrid fusion, score normalization, source authority weighting,
hard security gating, deduplication, requirement coverage matrices, conflict detection,
adversarial isolation, and performance benchmarks.
"""

import time
import pytest
from securoxi.orchestrator import (
    AgentOrchestrator,
    EvidenceSourceType,
    EvidenceQualityTier,
    CoverageState,
    EvidenceRequirement,
    EvidenceFusionEngine,
)


@pytest.fixture
def orchestrator():
    return AgentOrchestrator()


@pytest.fixture
def fusion_engine():
    return EvidenceFusionEngine()


@pytest.fixture
def sample_requirements():
    return [
        EvidenceRequirement(requirement_id="REQ-1", topic="Kubernetes", mandatory=True),
        EvidenceRequirement(requirement_id="REQ-2", topic="AWS Security", mandatory=True),
        EvidenceRequirement(requirement_id="REQ-3", topic="Terraform", mandatory=False),
    ]


# =========================================================================
# 1. HARD SECURITY GATING
# =========================================================================

def test_evidence_fusion_hard_security_gate(fusion_engine, sample_requirements):
    """Guarantees that HIGH_RISK documents are excluded from trusted fused evidence."""
    raw_chunks = [
        {
            "chunk_id": "CHK-SAFE-01",
            "document_id": "RESUME-SARAH.PDF",
            "source": "RESUME",
            "source_type": "CANDIDATE_RESUME",
            "security_status": "SAFE",
            "content": "Sarah Miller - Senior Kubernetes and AWS Security expert.",
            "score": 0.95,
        },
        {
            "chunk_id": "CHK-MALICIOUS-01",
            "document_id": "RESUME-MAL.PDF",
            "source": "RESUME",
            "source_type": "CANDIDATE_RESUME",
            "security_status": "HIGH_RISK",
            "content": "Malicious payload attempt.",
            "score": 0.99,
        },
    ]

    fused = fusion_engine.fuse_evidence(
        raw_chunks=raw_chunks,
        requirements=sample_requirements,
        query="Senior Cloud Security Engineer",
        trusted_mode=True,
    )

    chunk_ids = [c.chunk_id for c in fused.ranked_items]
    assert "CHK-SAFE-01" in chunk_ids
    assert "CHK-MALICIOUS-01" not in chunk_ids


# =========================================================================
# 2. SOURCE AUTHORITY WEIGHTING & RERANKING
# =========================================================================

def test_evidence_fusion_source_authority_ranking(fusion_engine, sample_requirements):
    """
    Verifies that higher-authority sources (ATS_METADATA / DETERMINISTIC_SECURITY)
    outrank lower-authority sources (LLM_ADVISORY) even with lower raw score.
    """
    raw_chunks = [
        {
            "chunk_id": "CHK-ADVISORY-01",
            "document_id": "SUMMARY.TXT",
            "source": "AI_SUMMARY",
            "source_type": "LLM_ADVISORY",
            "security_status": "SAFE",
            "content": "Candidate has Kubernetes expertise.",
            "score": 0.95,
        },
        {
            "chunk_id": "CHK-ATS-01",
            "document_id": "ATS-RECORD-01",
            "source": "ATS",
            "source_type": "ATS_METADATA",
            "security_status": "SAFE",
            "content": "Verified production Kubernetes clearance in ATS record.",
            "score": 0.85,
        },
    ]

    fused = fusion_engine.fuse_evidence(
        raw_chunks=raw_chunks,
        requirements=sample_requirements,
        query="Kubernetes clearance",
    )

    # ATS (0.85 * 1.3 = 1.105) outranks Advisory (0.95 * 0.6 = 0.57)
    assert fused.ranked_items[0].chunk_id == "CHK-ATS-01"
    assert fused.ranked_items[0].normalized_score > fused.ranked_items[1].normalized_score


# =========================================================================
# 3. DEDUPLICATION & NEAR-DUPLICATES
# =========================================================================

def test_evidence_fusion_deduplication(fusion_engine, sample_requirements):
    """Verifies that identical/near-duplicate chunks are consolidated and counted."""
    raw_chunks = [
        {
            "chunk_id": "CHK-01",
            "document_id": "RESUME-A.PDF",
            "source": "RESUME",
            "source_type": "CANDIDATE_RESUME",
            "security_status": "SAFE",
            "content": "Sarah Miller - Senior Kubernetes Engineer.",
            "score": 0.9,
        },
        {
            "chunk_id": "CHK-02",
            "document_id": "RESUME-A.PDF",
            "source": "RESUME",
            "source_type": "CANDIDATE_RESUME",
            "security_status": "SAFE",
            "content": "Sarah Miller - Senior Kubernetes Engineer.",
            "score": 0.9,
        },
    ]

    fused = fusion_engine.fuse_evidence(
        raw_chunks=raw_chunks,
        requirements=sample_requirements,
        query="Sarah Miller",
    )

    assert len(fused.ranked_items) == 1
    assert fused.duplicates_removed == 1


# =========================================================================
# 4. REQUIREMENT COVERAGE MATRIX
# =========================================================================

def test_evidence_fusion_requirement_coverage_matrix(fusion_engine, sample_requirements):
    """Verifies structured requirement coverage matrix (COMPLETE vs MISSING)."""
    raw_chunks = [
        {
            "chunk_id": "CHK-K8S",
            "document_id": "RESUME-A.PDF",
            "source": "RESUME",
            "source_type": "CANDIDATE_RESUME",
            "security_status": "SAFE",
            "content": "Expert in Kubernetes architecture and AWS security deployments.",
            "score": 0.9,
        }
    ]

    fused = fusion_engine.fuse_evidence(
        raw_chunks=raw_chunks,
        requirements=sample_requirements,
        query="Senior Cloud Architect",
    )

    matrix_map = {r.topic: r.state for r in fused.requirement_matrix}
    assert matrix_map["Kubernetes"] == CoverageState.COMPLETE
    assert matrix_map["AWS Security"] == CoverageState.COMPLETE
    assert matrix_map["Terraform"] == CoverageState.MISSING
    assert fused.overall_coverage == pytest.approx(66.66, 0.1)


# =========================================================================
# 5. CONTRADICTION DETECTION
# =========================================================================

def test_evidence_fusion_conflict_detection(fusion_engine, sample_requirements):
    """Verifies that conflicting claims across sources are detected into EvidenceConflict."""
    raw_chunks = [
        {
            "chunk_id": "CHK-RESUME-EXP",
            "document_id": "RESUME-A.PDF",
            "source": "RESUME",
            "source_type": "CANDIDATE_RESUME",
            "security_status": "SAFE",
            "content": "Sarah Miller has 6 years experience in Cloud Security and Kubernetes.",
            "score": 0.9,
        },
        {
            "chunk_id": "CHK-ATS-EXP",
            "document_id": "ATS-RECORD-A",
            "source": "ATS",
            "source_type": "ATS_METADATA",
            "security_status": "SAFE",
            "content": "Official ATS profile indicates 3 years experience in Cloud Security.",
            "score": 0.9,
        },
    ]

    fused = fusion_engine.fuse_evidence(
        raw_chunks=raw_chunks,
        requirements=sample_requirements,
        query="Experience check",
    )

    assert len(fused.conflicts) >= 1
    assert fused.conflicts[0].topic == "Years of Experience"
    assert fused.quality_tier == EvidenceQualityTier.CONFLICTING


# =========================================================================
# 6. UNTRUSTED INVESTIGATION MODE
# =========================================================================

def test_evidence_fusion_untrusted_investigation_mode(fusion_engine, sample_requirements):
    """Verifies that in investigation mode (trusted_mode=False), HIGH_RISK chunks are preserved."""
    raw_chunks = [
        {
            "chunk_id": "CHK-SUSPICIOUS-01",
            "document_id": "SUSPECT-DOC.PDF",
            "source": "FORENSIC_EVIDENCE",
            "source_type": "ENTERPRISE_DOC",
            "security_status": "HIGH_RISK",
            "content": "Suspect payload found in Kubernetes container log.",
            "score": 0.8,
        }
    ]

    fused = fusion_engine.fuse_evidence(
        raw_chunks=raw_chunks,
        requirements=sample_requirements,
        query="Forensic investigation",
        trusted_mode=False,
    )

    assert len(fused.ranked_items) == 1
    assert fused.ranked_items[0].security_status == "HIGH_RISK"


# =========================================================================
# 7. PERFORMANCE BENCHMARKS
# =========================================================================

def test_evidence_fusion_performance_benchmarks(fusion_engine, sample_requirements):
    """Benchmarks evidence fusion and reranking latency (< 5ms for 50+ chunks)."""
    raw_chunks = [
        {
            "chunk_id": f"CHK-{i}",
            "document_id": f"DOC-{i // 5}",
            "source": "RESUME",
            "source_type": "CANDIDATE_RESUME",
            "security_status": "SAFE",
            "content": f"Candidate {i} with Kubernetes and AWS security expertise.",
            "score": 0.8 + (i % 20) * 0.01,
        }
        for i in range(50)
    ]

    start_time = time.time()
    for _ in range(20):
        fusion_engine.fuse_evidence(
            raw_chunks=raw_chunks,
            requirements=sample_requirements,
            query="Benchmark Fusion Query",
        )
    avg_latency_ms = (time.time() - start_time) / 20.0 * 1000.0

    assert avg_latency_ms < 5.0, f"Evidence fusion latency {avg_latency_ms:.2f}ms exceeded 5ms"
