"""
SECUROXI AI Intelligence 2.0 — Autonomous Task Execution Test Suite (Phase 4 Stage 18)
Validates asynchronous background execution, real-time stage progression, live counters,
human approval gates, pause/resume/cancellation, durable state, and tenant isolation.
"""

import time
import pytest
from fastapi.testclient import TestClient

from securoxi.api.app import app, orchestrator_instance


@pytest.fixture
def client():
    return TestClient(app)


# =========================================================================
# 1. ASYNCHRONOUS TASK SUBMISSION & PROGRESSION
# =========================================================================

def test_autonomous_task_submit_and_complete(client):
    """Verifies that submitting a task runs asynchronously and reaches COMPLETED."""
    chunks = [
        {
            "chunk_id": "CHK-01",
            "document_id": "K8S_SECURITY.PDF",
            "source": "DOCS",
            "security_status": "SAFE",
            "content": "Kubernetes cluster hardening requires RBAC, NetworkPolicies, and admission controllers.",
        }
    ]

    response = client.post(
        "/api/v1/agentic/task/submit",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        json={
            "objective": "What are the core controls for Kubernetes security hardening?",
            "retrieval_chunks": chunks,
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert "task_id" in data
    assert "run_id" in data
    assert data["status"] == "RUNNING"
    task_id = data["task_id"]

    # Poll status until complete (max 3 seconds)
    completed = False
    for _ in range(30):
        time.sleep(0.1)
        st_resp = client.get(
            f"/api/v1/agentic/task/{task_id}/status",
            headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        )
        assert st_resp.status_code == 200
        st = st_resp.json()

        assert "stages" in st
        assert "counters" in st
        assert "events" in st

        if st["status"] == "COMPLETED":
            completed = True
            assert st["result"] is not None
            assert st["progress_percent"] == 100
            assert st["counters"]["safe_documents"] >= 1
            break

    assert completed is True


# =========================================================================
# 2. PAUSE & RESUME CONTROLS
# =========================================================================

def test_autonomous_task_pause_and_resume(client):
    """Verifies that a running task can be paused and resumed."""
    # Submit task with longer chunks
    response = client.post(
        "/api/v1/agentic/task/submit",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        json={
            "objective": "Evaluate candidate cloud experience.",
            "retrieval_chunks": [{"chunk_id": "C-1", "document_id": "doc.pdf", "content": "Experience"}],
        },
    )
    task_id = response.json()["task_id"]

    # Pause task
    p_resp = client.post(
        f"/api/v1/agentic/task/{task_id}/pause",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
    )
    assert p_resp.status_code == 200
    assert p_resp.json()["status"] == "PAUSED"

    # Verify status is PAUSED
    st = client.get(
        f"/api/v1/agentic/task/{task_id}/status",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
    ).json()
    assert st["status"] == "PAUSED"

    # Resume task
    r_resp = client.post(
        f"/api/v1/agentic/task/{task_id}/resume",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
    )
    assert r_resp.status_code == 200
    assert r_resp.json()["status"] == "RUNNING"

    # Wait for completion
    for _ in range(30):
        time.sleep(0.05)
        st = client.get(
            f"/api/v1/agentic/task/{task_id}/status",
            headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        ).json()
        if st["status"] in ["COMPLETED", "FAILED", "CANCELLED"]:
            break


# =========================================================================
# 3. CANCELLATION CONTROLS
# =========================================================================

def test_autonomous_task_cancellation(client):
    """Verifies that a task can be cancelled gracefully."""
    response = client.post(
        "/api/v1/agentic/task/submit",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        json={
            "objective": "Screen all incoming resumes.",
            "retrieval_chunks": [{"chunk_id": "C-1", "document_id": "doc.pdf", "content": "Text"}],
        },
    )
    task_id = response.json()["task_id"]

    # Cancel task
    c_resp = client.post(
        f"/api/v1/agentic/task/{task_id}/cancel",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
    )
    assert c_resp.status_code == 200
    assert c_resp.json()["status"] == "CANCELLED"

    st = client.get(
        f"/api/v1/agentic/task/{task_id}/status",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
    ).json()
    assert st["status"] == "CANCELLED"


# =========================================================================
# 4. HUMAN APPROVAL GATES
# =========================================================================

def test_autonomous_task_human_approval_gate(client):
    """Verifies that WAITING_FOR_APPROVAL blocks until user approves."""
    response = client.post(
        "/api/v1/agentic/task/submit",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        json={"objective": "Advance candidate Sarah Miller to final offer."},
    )
    task_id = response.json()["task_id"]

    # Trigger approval request
    appr_id = orchestrator_instance.execution_runner.request_human_approval(
        task_id=task_id,
        action_summary="Advance 1 candidate to offer stage",
        payload={"candidate_id": "CAND-01", "role": "Senior Cloud Security Engineer"},
        tenant_id="TENANT-01",
    )

    st = client.get(
        f"/api/v1/agentic/task/{task_id}/status",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
    ).json()
    assert st["status"] == "WAITING_FOR_APPROVAL"
    assert st["approval_request"]["approval_id"] == appr_id

    # Decide approval
    dec_resp = client.post(
        f"/api/v1/agentic/task/{task_id}/approval/decide",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        json={
            "approval_id": appr_id,
            "approved": True,
            "reason": "Recruiting Manager Approved",
        },
    )
    assert dec_resp.status_code == 200
    assert dec_resp.json()["status"] == "APPROVED"

    # Wait for completion
    for _ in range(30):
        time.sleep(0.05)
        st = client.get(
            f"/api/v1/agentic/task/{task_id}/status",
            headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        ).json()
        if st["status"] in ["COMPLETED", "FAILED", "CANCELLED"]:
            break


# =========================================================================
# 5. TENANT ISOLATION
# =========================================================================

def test_autonomous_task_cross_tenant_access_denied(client):
    """Verifies that accessing another tenant's task returns 404."""
    response = client.post(
        "/api/v1/agentic/task/submit",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        json={"objective": "Tenant 01 private task."},
    )
    task_id = response.json()["task_id"]

    # Access with TENANT-02 header must be rejected
    denied = client.get(
        f"/api/v1/agentic/task/{task_id}/status",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-02"},
    )
    assert denied.status_code == 404

    # Wait for completion
    for _ in range(30):
        time.sleep(0.05)
        st = client.get(
            f"/api/v1/agentic/task/{task_id}/status",
            headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        ).json()
        if st["status"] in ["COMPLETED", "FAILED", "CANCELLED"]:
            break
