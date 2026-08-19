"""
SECUROXI AI Intelligence 2.0 — Controlled Autonomous Action Test Suite (Phase 8 Stage 52)
Validates guarded autonomy levels, human approval gates, security clearance barriers,
stale action rejection, idempotency, and operational kill switch enforcement.
"""

import pytest
from securoxi.enterprise.autonomy import (
    ControlledAutonomyEngine,
    AutonomyLevel,
    ActionImpactClass,
    ActionReversibility,
    ProposalStatus,
    ExecutionStatus,
)


# =========================================================================
# 1. GUARDED LOW-IMPACT AUTONOMY & HIGH-IMPACT APPROVAL GATES
# =========================================================================

def test_guarded_autonomy_and_approval_gates():
    """Verifies that low-impact actions run under L3 guarded autonomy, while high-impact actions require human approval."""
    engine = ControlledAutonomyEngine()

    # 1. Low-impact action (Index refresh) -> Executes autonomously
    low_prop = engine.propose_action(
        organization_id="ORG-TEST",
        workspace_id="WS-MAIN",
        action_type="REFRESH_SEARCH_INDEX",
        target_resource_id="IDX-001",
        impact_class=ActionImpactClass.LOW_IMPACT_REVERSIBLE,
        autonomy_level=AutonomyLevel.L3_GUARDED_AUTONOMOUS_LOW_IMPACT,
    )
    ok, exec_rec, reason = engine.execute_action(low_prop.proposal_id, current_evidence_version=1)
    assert ok is True
    assert exec_rec is not None
    assert exec_rec.status == ExecutionStatus.SUCCESS

    # 2. High-impact action (ATS stage advance) -> Requires approval (L2)
    high_prop = engine.propose_action(
        organization_id="ORG-TEST",
        workspace_id="WS-MAIN",
        action_type="ADVANCE_ATS_STAGE",
        target_resource_id="CAND-101",
        impact_class=ActionImpactClass.HIGH_IMPACT,
    )
    assert high_prop.autonomy_level == AutonomyLevel.L2_HUMAN_APPROVAL_REQUIRED

    # Attempting to execute without approver -> Denied
    ok, _, reason = engine.execute_action(high_prop.proposal_id, current_evidence_version=1)
    assert ok is False
    assert reason == "APPROVAL_REQUIRED"

    # Executing with human approver -> Succeeded
    ok, exec_rec, reason = engine.execute_action(high_prop.proposal_id, current_evidence_version=1, approver_id="USER-RECRUITER-1")
    assert ok is True
    assert exec_rec.executed_by == "USER-RECRUITER-1"


# =========================================================================
# 2. SECURITY CLEARANCE GATES & STALE PROPOSAL PROTECTION
# =========================================================================

def test_security_clearance_and_stale_protection():
    """Verifies that actions targeting HIGH_RISK entities or based on stale evidence are blocked."""
    engine = ControlledAutonomyEngine()

    prop = engine.propose_action(
        organization_id="ORG-TEST",
        workspace_id="WS-MAIN",
        action_type="REFRESH_CANDIDATE_DATA",
        target_resource_id="CAND-MALICIOUS",
        source_evidence_version=1,
    )

    # 1. Target is HIGH_RISK -> Blocked deterministically
    ok, _, reason = engine.execute_action(
        proposal_id=prop.proposal_id,
        current_evidence_version=1,
        target_security_state="HIGH_RISK",
    )
    assert ok is False
    assert "HIGH_RISK" in reason

    # 2. Evidence version changed (v2 != v1) -> Blocked as STALE_PROPOSAL
    ok, _, reason = engine.execute_action(
        proposal_id=prop.proposal_id,
        current_evidence_version=2,
        target_security_state="SAFE",
    )
    assert ok is False
    assert reason == "STALE_PROPOSAL"


# =========================================================================
# 3. IDEMPOTENCY GUARD & OPERATIONAL KILL SWITCH
# =========================================================================

def test_idempotency_and_operational_safe_mode():
    """Verifies duplicate execution prevention and safe mode kill switch enforcement."""
    engine = ControlledAutonomyEngine()

    prop = engine.propose_action(
        organization_id="ORG-TEST",
        workspace_id="WS-MAIN",
        action_type="FLUSH_WORKFLOW_CACHE",
        target_resource_id="CACHE-001",
    )

    # Execute once -> Succeeded
    ok, _, _ = engine.execute_action(prop.proposal_id, current_evidence_version=1)
    assert ok is True

    # Duplicate execution attempt with same idempotency key -> Blocked
    ok, _, reason = engine.execute_action(prop.proposal_id, current_evidence_version=1)
    assert ok is False
    assert reason == "DUPLICATE_IDEMPOTENCY"

    # Enable Safe Mode (Kill Switch)
    engine.set_safe_mode(True)
    prop2 = engine.propose_action(
        organization_id="ORG-TEST",
        workspace_id="WS-MAIN",
        action_type="REVALIDATE_DATA",
        target_resource_id="RES-002",
    )
    ok, _, reason = engine.execute_action(prop2.proposal_id, current_evidence_version=1)
    assert ok is False
    assert reason == "SAFE_MODE_BLOCKED"
