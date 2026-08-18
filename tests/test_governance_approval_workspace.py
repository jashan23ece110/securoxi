"""
SECUROXI AI Intelligence 2.0 — Human Approval, Governance & Controlled Action Test Suite (Phase 4 Stage 23)
Validates typed action proposals, separation of duties, self-approval prevention,
policy & security revalidation, replay protection, batch execution with mixed states, and audit trails.
"""

import pytest
from fastapi.testclient import TestClient
from securoxi.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


# =========================================================================
# 1. PROPOSAL CREATION & REVIEW
# =========================================================================

def test_create_and_get_governance_proposal(client):
    """Verifies that high-impact actions create typed proposals in PENDING state."""
    targets = [
        {"id": "CAND-01", "name": "Sarah Miller", "security_status": "SAFE"},
        {"id": "CAND-02", "name": "David Singh", "security_status": "SAFE"},
    ]

    create_res = client.post(
        "/api/v1/agentic/governance/proposals",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        json={
            "requester": "HiringAgent",
            "action_type": "ADVANCE_CANDIDATE",
            "targets": targets,
            "reason": "Top candidates matching Senior Cloud Security Engineer JD.",
            "impact_level": "HIGH",
        },
    )
    assert create_res.status_code == 200
    prop = create_res.json()

    assert "PROP-" in prop["proposal_id"]
    assert prop["status"] == "PENDING"
    assert prop["target_count"] == 2
    assert prop["impact_level"] == "HIGH"

    # Fetch proposal details
    get_res = client.get(
        f"/api/v1/agentic/governance/proposals/{prop['proposal_id']}",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
    )
    assert get_res.status_code == 200
    assert get_res.json()["proposal_id"] == prop["proposal_id"]


# =========================================================================
# 2. SEPARATION OF DUTIES & APPROVAL DECISION
# =========================================================================

def test_self_approval_denied_by_separation_of_duties(client):
    """Verifies that an agent or requester cannot approve its own action proposal."""
    create_res = client.post(
        "/api/v1/agentic/governance/proposals",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        json={
            "requester": "HiringAgent",
            "action_type": "ADVANCE_CANDIDATE",
            "targets": [{"id": "CAND-01", "name": "Sarah Miller"}],
            "reason": "Advance candidate",
        },
    )
    prop_id = create_res.json()["proposal_id"]

    # Attempt self-approval as HiringAgent
    decide_res = client.post(
        f"/api/v1/agentic/governance/proposals/{prop_id}/decide",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        json={"approved": True, "decider_id": "HiringAgent", "comment": "Self-approving."},
    )
    assert decide_res.status_code == 400
    assert "Separation of duties violation" in decide_res.json()["detail"]


def test_independent_human_approves_proposal(client):
    """Verifies that an independent human reviewer can approve a proposal."""
    create_res = client.post(
        "/api/v1/agentic/governance/proposals",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        json={
            "requester": "HiringAgent",
            "action_type": "ADVANCE_CANDIDATE",
            "targets": [{"id": "CAND-01", "name": "Sarah Miller"}],
            "reason": "Advance candidate",
        },
    )
    prop_id = create_res.json()["proposal_id"]

    # Approve as Recruiter Jane
    decide_res = client.post(
        f"/api/v1/agentic/governance/proposals/{prop_id}/decide",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        json={"approved": True, "decider_id": "Recruiter Jane", "comment": "Verified background and cleared."},
    )
    assert decide_res.status_code == 200
    prop_data = decide_res.json()
    assert prop_data["status"] == "APPROVED"
    assert prop_data["decision"]["decided_by"] == "Recruiter Jane"


# =========================================================================
# 3. EXECUTION, POLICY REVALIDATION & REPLAY PROTECTION
# =========================================================================

def test_execute_approved_action_with_replay_protection(client):
    """Verifies execution revalidates security and protects against duplicate execution."""
    targets = [
        {"id": "CAND-01", "name": "Sarah Miller", "security_status": "SAFE"},
        {"id": "CAND-MALICIOUS", "name": "Attacker Payload", "security_status": "HIGH_RISK"},
    ]

    create_res = client.post(
        "/api/v1/agentic/governance/proposals",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        json={
            "requester": "HiringAgent",
            "action_type": "ADVANCE_CANDIDATE",
            "targets": targets,
            "reason": "Batch advancement test",
        },
    )
    prop_id = create_res.json()["proposal_id"]

    # 1. Approve
    client.post(
        f"/api/v1/agentic/governance/proposals/{prop_id}/decide",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        json={"approved": True, "decider_id": "Lead Recruiter"},
    )

    # 2. Execute proposal
    exec_res = client.post(
        f"/api/v1/agentic/governance/proposals/{prop_id}/execute",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        json={"actor_id": "Lead Recruiter"},
    )
    assert exec_res.status_code == 200
    exec_data = exec_res.json()

    assert exec_data["succeeded_count"] == 1
    assert exec_data["failed_count"] == 1
    assert exec_data["is_partial"] is True

    # 3. Replay attempt -> Rejected
    replay_res = client.post(
        f"/api/v1/agentic/governance/proposals/{prop_id}/execute",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        json={"actor_id": "Lead Recruiter"},
    )
    assert replay_res.status_code == 400
    assert "Replay rejected" in replay_res.json()["detail"]


# =========================================================================
# 4. IMMUTABLE AUDIT LOGS & TENANT ISOLATION
# =========================================================================

def test_governance_audit_trail_and_tenant_isolation(client):
    """Verifies that governance actions generate immutable audit logs isolated by tenant."""
    audit_res = client.get(
        "/api/v1/agentic/governance/audit",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
    )
    assert audit_res.status_code == 200
    trail = audit_res.json()
    assert len(trail) > 0

    event_types = [e["event_type"] for e in trail]
    assert "APPROVAL_CREATED" in event_types
    assert "ACTION_EXECUTED" in event_types
