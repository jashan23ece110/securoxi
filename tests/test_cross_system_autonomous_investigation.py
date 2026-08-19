"""
SECUROXI AI Intelligence 2.0 — Cross-System Autonomous Investigation Test Suite (Phase 8 Stage 49)
Validates case initiation, cross-system timeline construction, competing hypothesis evaluation,
governed recommendation synthesis, and multi-tenant isolation.
"""

import pytest
import time
from securoxi.enterprise.investigation import (
    CrossSystemInvestigationEngine,
    TriggerType,
    TriggerSignificance,
    InvestigationStatus,
    HypothesisStatus,
    InvestigationFindingClass,
    ResponseActionType,
)


# =========================================================================
# 1. INVESTIGATION INITIATION & CHRONOLOGICAL TIMELINE
# =========================================================================

def test_investigation_initiation_and_timeline():
    """Verifies case creation with budget bounds and cross-system timeline event recording."""
    engine = CrossSystemInvestigationEngine()

    case = engine.initiate_case(
        organization_id="ORG-ALPHA",
        workspace_id="WS-SECURITY",
        trigger_type=TriggerType.REPEATED_SECURITY_FINDINGS,
        target_resource_id="CAND-404",
        significance=TriggerSignificance.HIGH,
        max_budget_steps=5,
    )
    assert case.status == InvestigationStatus.INITIATED
    assert case.max_budget_steps == 5

    # Append Timeline Events across systems
    t1 = engine.add_timeline_event(case.case_id, "ATS", "Resume uploaded via Greenhouse", provenance="GH-EVT-101")
    t2 = engine.add_timeline_event(case.case_id, "SECURITY", "Obfuscated prompt injection detected", provenance="SCAN-EVT-202")
    t3 = engine.add_timeline_event(case.case_id, "POLICY", "Automated ATS write stage advance blocked by policy", provenance="POL-EVT-303")

    assert len(case.timeline) == 3
    assert case.steps_executed == 3


# =========================================================================
# 2. COMPETING HYPOTHESES EVALUATION
# =========================================================================

def test_competing_hypotheses_testing():
    """Verifies formulation of competing hypotheses and evidence-based resolution."""
    engine = CrossSystemInvestigationEngine()

    case = engine.initiate_case(
        organization_id="ORG-ALPHA",
        workspace_id="WS-SECURITY",
        trigger_type=TriggerType.CANDIDATE_SECURITY_ESCALATION,
        target_resource_id="CAND-404",
    )

    # Propose Competing Hypotheses
    hyp1 = engine.propose_hypothesis(case.case_id, "Deliberate prompt injection attack to bypass ATS screening")
    hyp2 = engine.propose_hypothesis(case.case_id, "Benign Markdown formatting artifact")

    assert len(case.hypotheses) == 2

    # Test Hypotheses against collected security logs
    tested = engine.test_hypotheses(
        case_id=case.case_id,
        supported_hypothesis_id=hyp1.hypothesis_id,
        supporting_evidence=["Hidden Unicode tag matching known jailbreak syntax", "Obfuscated base64 instruction in metadata"],
        contradicting_evidence=["Parser syntax error rate 0%"],
    )
    assert tested is True
    assert hyp1.status == HypothesisStatus.SUPPORTED
    assert hyp1.confidence >= 0.90
    assert hyp2.status == HypothesisStatus.REFUTED


# =========================================================================
# 3. GOVERNED RECOMMENDATION SYNTHESIS & TENANT ISOLATION
# =========================================================================

def test_recommendation_synthesis_and_tenant_isolation():
    """Verifies governed recommendation generation and strict multi-tenant boundary checks."""
    engine = CrossSystemInvestigationEngine()

    case = engine.initiate_case(
        organization_id="ORG-ALPHA",
        workspace_id="WS-SECURITY",
        trigger_type=TriggerType.SUSPICIOUS_ATS_ACTIVITY,
        target_resource_id="CAND-404",
    )

    # Synthesize Final Finding & Recommendation
    rec = engine.synthesize_and_recommend(
        case_id=case.case_id,
        finding_class=InvestigationFindingClass.CONFIRMED_SECURITY_ISSUE,
        action_type=ResponseActionType.QUARANTINE_RESOURCE,
        reason="Verified prompt injection attack attempting privilege escalation in ATS pipeline",
    )
    assert rec is not None
    assert rec.requires_approval is True  # Consequential action requires Stage 23 Human Approval
    assert case.status == InvestigationStatus.COMPLETED
    assert case.finding_class == InvestigationFindingClass.CONFIRMED_SECURITY_ISSUE

    # Tenant Isolation: Org Beta cannot view Org Alpha cases
    assert len(engine.get_cases("ORG-BETA")) == 0
    assert len(engine.get_cases("ORG-ALPHA")) == 1
