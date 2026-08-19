"""
SECUROXI AI Intelligence 2.0 — Enterprise Control Plane Test Suite (Phase 9 Stage 54)
Validates policy registration & rollback, capability registry evaluation gates,
unified decision context evaluation, and strict multi-tenant scoping.
"""

import pytest
from securoxi.enterprise.controlplane import (
    EnterpriseControlPlane,
    PolicyDomain,
    PolicyStatus,
    CapabilityStatus,
    EvaluationGateState,
    ControlPlaneDecision,
)


# =========================================================================
# 1. POLICY REGISTRATION & VERSIONED ROLLBACK
# =========================================================================

def test_policy_registration_and_rollback():
    """Verifies registering declarative policies and rolling them back with version tracking."""
    cp = EnterpriseControlPlane()

    # 1. Register Policy
    pol = cp.register_policy(
        organization_id="ORG-TEST",
        domain=PolicyDomain.SECURITY,
        rules={"mandatory_mfa": True, "strict_clearance": True},
    )
    assert pol.status == PolicyStatus.ACTIVE
    assert pol.version == 1

    # 2. Rollback Policy -> Old becomes ROLLED_BACK, new active policy version created
    new_pol = cp.rollback_policy(pol.policy_id)
    assert new_pol is not None
    assert new_pol.version == 2
    assert pol.status == PolicyStatus.ROLLED_BACK
    assert new_pol.status == PolicyStatus.ACTIVE


# =========================================================================
# 2. CAPABILITY REGISTRY & EVALUATION GATE
# =========================================================================

def test_capability_registry_evaluation_gate():
    """Verifies that capabilities failing Stage 33 evaluation are forced to DISABLED status."""
    cp = EnterpriseControlPlane()

    # 1. Passing Capability -> ENABLED
    cap_pass = cp.register_capability(
        organization_id="ORG-TEST",
        name="Candidate Resume Scanner",
        category="AGENT",
        required_permissions=["candidate:read"],
        evaluation_state=EvaluationGateState.PASS,
    )
    assert cap_pass.status == CapabilityStatus.ENABLED

    # 2. Failing Capability -> DISABLED
    cap_fail = cp.register_capability(
        organization_id="ORG-TEST",
        name="Experimental Auto-Reject Agent",
        category="AGENT",
        required_permissions=["candidate:write"],
        evaluation_state=EvaluationGateState.FAIL,
    )
    assert cap_fail.status == CapabilityStatus.DISABLED


# =========================================================================
# 3. UNIFIED DECISION CONTEXT & TENANT ISOLATION
# =========================================================================

def test_unified_decision_evaluation_and_tenant_isolation():
    """Verifies decision evaluation across Security, Safe Mode, Evaluation, and Approval gates."""
    cp = EnterpriseControlPlane()

    # 1. Security Barrier: Target is HIGH_RISK -> DENY
    snap1 = cp.evaluate_decision(
        organization_id="ORG-ALPHA",
        workspace_id="WS-MAIN",
        actor_id="USER-1",
        requested_action="READ_DOCUMENT",
        target_security_state="HIGH_RISK",
    )
    assert snap1.decision == ControlPlaneDecision.DENY

    # 2. Stage 33 Evaluation Barrier: Capability evaluation is FAIL -> DENY
    snap2 = cp.evaluate_decision(
        organization_id="ORG-ALPHA",
        workspace_id="WS-MAIN",
        actor_id="USER-1",
        requested_action="RUN_WORKFLOW",
        target_security_state="SAFE",
        evaluation_state=EvaluationGateState.FAIL,
    )
    assert snap2.decision == ControlPlaneDecision.DENY

    # 3. High-Impact Action Gate -> REQUIRE_APPROVAL
    snap3 = cp.evaluate_decision(
        organization_id="ORG-ALPHA",
        workspace_id="WS-MAIN",
        actor_id="USER-1",
        requested_action="ADVANCE_ATS_STAGE",
        target_security_state="SAFE",
        is_high_impact=True,
    )
    assert snap3.decision == ControlPlaneDecision.REQUIRE_APPROVAL

    # 4. Safe Mode Activated -> All actions REQUIRE_APPROVAL
    cp.set_safe_mode(True)
    snap4 = cp.evaluate_decision(
        organization_id="ORG-ALPHA",
        workspace_id="WS-MAIN",
        actor_id="USER-1",
        requested_action="REFRESH_INDEX",
        target_security_state="SAFE",
    )
    assert snap4.decision == ControlPlaneDecision.REQUIRE_APPROVAL

    # Tenant Isolation: Org Beta cannot see Org Alpha policies
    cp.register_policy("ORG-ALPHA", PolicyDomain.HIRING_ATS, {"rules": "alpha"})
    assert len(cp.get_policies("ORG-BETA")) == 0
    assert len(cp.get_policies("ORG-ALPHA")) >= 1
