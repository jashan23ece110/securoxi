"""
SECUROXI AI Intelligence 2.0 — Production Feedback & Controlled Adaptive Improvement Test Suite (Stage 34)
Validates feedback ingestion, triage, clustering, Stage 33 quality gate evaluation,
human governance approval, canary deployment, and strict prevention of autonomous self-modification.
"""

import pytest
from securoxi.orchestrator.feedback import (
    ControlledAdaptiveImprovementEngine,
    FeedbackEvent,
    FeedbackCategory,
    FeedbackSource,
    FeedbackSeverity,
    FeedbackValidationState,
    ImprovementStatus,
)
from securoxi.orchestrator.evaluation import ContinuousEvaluationEngine


# =========================================================================
# 1. END-TO-END CONTROLLED ADAPTIVE IMPROVEMENT LIFECYCLE
# =========================================================================

def test_controlled_adaptive_improvement_lifecycle():
    """Verifies complete governed improvement pipeline from feedback to canary release."""
    eval_engine = ContinuousEvaluationEngine()
    engine = ControlledAdaptiveImprovementEngine(evaluation_engine=eval_engine)

    # 1. Ingest Recruiter Feedback
    fb = FeedbackEvent(
        tenant_id="TENANT-01",
        actor="recruiter@enterprise.com",
        source=FeedbackSource.RECRUITER,
        category=FeedbackCategory.WRONG_REQUIREMENT_MATCH,
        severity=FeedbackSeverity.HIGH,
        affected_component="HIRING_AGENT",
        comment="Kubernetes skill was missed on resume with unusual formatting.",
    )
    fb_id = engine.record_feedback(fb)
    assert fb_id == fb.feedback_id

    # 2. Triage & Analyst Validation
    validated = engine.triage_and_validate(fb_id, is_valid=True, notes="Confirmed parser missed section heading.")
    assert validated is True
    assert engine._feedback_events[fb_id].validation_state == FeedbackValidationState.VALIDATED

    # 3. Cluster Feedback
    clusters = engine.cluster_feedback(tenant_id="TENANT-01")
    assert len(clusters) == 1
    cluster = clusters[0]
    assert cluster.frequency == 1
    assert cluster.affected_component == "HIRING_AGENT"

    # 4. Create Improvement Candidate
    candidate = engine.create_improvement_candidate(
        cluster_id=cluster.cluster_id,
        proposed_change="Add regex heading matcher for formatted skills section",
        expected_benefit="Increase Kubernetes requirement recall by 15%",
    )
    assert candidate is not None
    assert candidate.status == ImprovementStatus.PROPOSED

    # 5. Evaluate Candidate against Stage 33 Quality Gates
    passing_metrics = {
        "security_critical_bypasses": 0.0,
        "security_detection_rate": 1.0,
        "grounding_citation_accuracy": 1.0,
        "hiring_mandatory_gating_accuracy": 1.0,
        "latency_p95_ms": 190.0,
    }
    passed_eval = engine.evaluate_improvement(candidate.candidate_id, passing_metrics)
    assert passed_eval is True
    assert candidate.status == ImprovementStatus.UNDER_REVIEW

    # 6. Apply Human Governance Approval
    approved = engine.approve_improvement(candidate.candidate_id, approver_id="security-lead@enterprise.com")
    assert approved is True
    assert candidate.status == ImprovementStatus.APPROVED

    # 7. Canary Release
    released = engine.canary_release(candidate.candidate_id, version="v2.0.1-canary")
    assert released is True
    assert candidate.status == ImprovementStatus.RELEASED
    assert candidate.release_version == "v2.0.1-canary"


# =========================================================================
# 2. NO AUTONOMOUS PRODUCTION SELF-MODIFICATION
# =========================================================================

def test_unapproved_candidate_cannot_be_released():
    """Verifies that an unapproved improvement candidate cannot be released directly."""
    engine = ControlledAdaptiveImprovementEngine()

    fb = FeedbackEvent(
        tenant_id="TENANT-01",
        category=FeedbackCategory.FALSE_POSITIVE,
        affected_component="SECURITY_AGENT",
        comment="White text in header flagged as injection",
    )
    fb_id = engine.record_feedback(fb)
    engine.triage_and_validate(fb_id, is_valid=True)
    clusters = engine.cluster_feedback()
    candidate = engine.create_improvement_candidate(
        cluster_id=clusters[0].cluster_id,
        proposed_change="Refine white text threshold",
        expected_benefit="Reduce false positives",
    )

    # Attempting to release directly without evaluation and approval must fail
    released = engine.canary_release(candidate.candidate_id, version="v2.0.1-unapproved")
    assert released is False
    assert candidate.status == ImprovementStatus.PROPOSED
