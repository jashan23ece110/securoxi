"""
SECUROXI AI Intelligence 2.0 — Cross-Document Reasoning & Research Synthesis Test Suite
Validates direct answer synthesis, structured entity comparison matrices, ranking explanations,
derived claim provenance, conflict preservation, qualified claim integration, and performance benchmarks.
"""

import time
import pytest
from securoxi.orchestrator import (
    AgentOrchestrator,
    SynthesisMode,
    SynthesisStatus,
    ClaimType,
    EvidenceSupportState,
    GroundednessState,
    AnswerStatus,
    Claim,
    Citation,
    VerifiedEvidencePackage,
    ResearchSynthesizer,
)


@pytest.fixture
def orchestrator():
    return AgentOrchestrator()


@pytest.fixture
def synthesizer():
    return ResearchSynthesizer()


@pytest.fixture
def sample_verified_package():
    return VerifiedEvidencePackage(
        query="Senior Cloud Security Engineer",
        groundedness_state=GroundednessState.FULLY_GROUNDED,
        answer_status=AnswerStatus.GROUNDED,
        verified_claims=[
            Claim(
                claim_id="CLM-01",
                text="Sarah Miller has 6 years experience in production Kubernetes cluster security",
                claim_type=ClaimType.FACTUAL,
                subject="Sarah Miller",
                is_verified=True,
                support_state=EvidenceSupportState.DIRECTLY_SUPPORTED,
            ),
            Claim(
                claim_id="CLM-02",
                text="Sarah Miller has verified AWS VPC security and container isolation expertise",
                claim_type=ClaimType.FACTUAL,
                subject="Sarah Miller",
                is_verified=True,
                support_state=EvidenceSupportState.DIRECTLY_SUPPORTED,
            ),
        ],
        citations=[
            Citation(
                citation_id="CIT-01",
                document_id="RESUME-SARAH.PDF",
                chunk_id="CHK-01",
                source="RESUME",
                snippet="Sarah Miller - Senior Cloud Security Engineer with 6 years Kubernetes experience.",
                is_valid=True,
            )
        ],
    )


# =========================================================================
# 1. DIRECT ANSWER SYNTHESIS
# =========================================================================

def test_direct_synthesis_mode(synthesizer, sample_verified_package):
    """Verifies that direct synthesis generates an evidence-grounded answer with citations."""
    result = synthesizer.synthesize(
        package=sample_verified_package,
        mode=SynthesisMode.DIRECT_ANSWER,
    )

    assert result.mode == SynthesisMode.DIRECT_ANSWER.value
    assert result.status == SynthesisStatus.COMPLETED
    assert "Sarah Miller" in result.detailed_answer
    assert len(result.citations) >= 1
    assert len(result.derived_claims) >= 1


# =========================================================================
# 2. STRUCTURED COMPARISON MATRIX
# =========================================================================

def test_comparison_mode_matrix_generation(synthesizer, sample_verified_package):
    """Verifies that comparison mode generates a structured dimension-by-dimension comparison."""
    entities = [
        {"name": "Sarah Miller", "security_status": "SAFE", "k8s_experience": "6 Years (Verified)", "fit_score": 96},
        {"name": "David Chen", "security_status": "SAFE", "k8s_experience": "3 Years (Partial)", "fit_score": 88},
    ]

    result = synthesizer.synthesize(
        package=sample_verified_package,
        mode=SynthesisMode.COMPARISON,
        comparison_entities=entities,
    )

    assert result.mode == SynthesisMode.COMPARISON.value
    assert len(result.comparisons) == 3
    dims = [c.dimension for c in result.comparisons]
    assert "Security Clearance" in dims
    assert "Kubernetes Experience" in dims
    assert "Fit Score" in dims
    assert "Sarah Miller is recommended" in result.detailed_answer


# =========================================================================
# 3. RANKING EXPLANATION
# =========================================================================

def test_ranking_explanation_mode(synthesizer, sample_verified_package):
    """Verifies that ranking explanation synthesizes justification based on authoritative fit scores."""
    result = synthesizer.synthesize(
        package=sample_verified_package,
        mode=SynthesisMode.RANKING_EXPLANATION,
    )

    assert result.mode == SynthesisMode.RANKING_EXPLANATION.value
    assert "ranked #1" in result.detailed_answer
    assert len(result.recommendations) > 0


# =========================================================================
# 4. DERIVED CLAIMS PROVENANCE
# =========================================================================

def test_derived_claims_provenance(synthesizer, sample_verified_package):
    """Verifies that derived claims retain provenance linking back to underlying verified claims."""
    result = synthesizer.synthesize(
        package=sample_verified_package,
        mode=SynthesisMode.SUMMARY,
    )

    assert len(result.derived_claims) >= 1
    derived = result.derived_claims[0]
    assert "CLM-01" in derived.source_claim_ids
    assert derived.is_reverified is True


# =========================================================================
# 5. CONFLICT PRESERVATION
# =========================================================================

def test_conflict_preservation_in_synthesis(synthesizer):
    """Verifies that unresolved conflicts in the evidence package are preserved in the synthesis result."""
    conflicting_package = VerifiedEvidencePackage(
        query="Experience check",
        groundedness_state=GroundednessState.PARTIALLY_GROUNDED,
        answer_status=AnswerStatus.CONFLICTING,
        conflicts=[{"topic": "Years of Experience", "claim_a": "6 years", "claim_b": "3 years"}],
    )

    result = synthesizer.synthesize(
        package=conflicting_package,
        mode=SynthesisMode.DIRECT_ANSWER,
    )

    assert result.status == SynthesisStatus.CONFLICTING
    assert len(result.unresolved_conflicts) >= 1


# =========================================================================
# 6. INSUFFICIENT EVIDENCE HANDLING
# =========================================================================

def test_insufficient_evidence_handling(synthesizer):
    """Verifies that packages without verified claims produce an explicit insufficient evidence notice."""
    empty_package = VerifiedEvidencePackage(
        query="CISSP Certification",
        groundedness_state=GroundednessState.INSUFFICIENTLY_GROUNDED,
        answer_status=AnswerStatus.INSUFFICIENT_EVIDENCE,
        verified_claims=[],
    )

    result = synthesizer.synthesize(
        package=empty_package,
        mode=SynthesisMode.DIRECT_ANSWER,
    )

    assert result.status == SynthesisStatus.INSUFFICIENT_EVIDENCE
    assert "could not find sufficient supporting evidence" in result.detailed_answer


# =========================================================================
# 7. PERFORMANCE BENCHMARKS
# =========================================================================

def test_cross_document_reasoning_performance_benchmarks(synthesizer, sample_verified_package):
    """Benchmarks research synthesis and comparison matrix generation latency (< 5ms)."""
    start_time = time.time()
    for _ in range(20):
        synthesizer.synthesize(
            package=sample_verified_package,
            mode=SynthesisMode.COMPARISON,
            comparison_entities=[
                {"name": "Sarah Miller", "security_status": "SAFE", "k8s_experience": "6 Years", "fit_score": 96},
                {"name": "David Chen", "security_status": "SAFE", "k8s_experience": "3 Years", "fit_score": 88},
            ],
        )
    avg_latency_ms = (time.time() - start_time) / 20.0 * 1000.0

    assert avg_latency_ms < 5.0, f"Research synthesis latency {avg_latency_ms:.2f}ms exceeded 5ms"
