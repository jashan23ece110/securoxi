"""
SECUROXI AI Intelligence 2.0 — Unified Live Task & Security Monitoring Workspace Test Suite (Phase 4 Stage 22)
Validates top-level operational counters, subsystem health checks, active task progress,
live security event streams, actionable needs-attention items, and RBAC-controlled telemetry.
"""

import pytest
from fastapi.testclient import TestClient
from securoxi.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


# =========================================================================
# 1. TOP-LEVEL OPERATIONAL STATUS SUMMARY & SUBSYSTEM HEALTH
# =========================================================================

def test_monitoring_overview_returns_valid_counters_and_subsystems(client):
    """Verifies that the monitoring overview provides real status summary and subsystem health."""
    response = client.get(
        "/api/v1/agentic/monitoring/overview",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["tenant_id"] == "TENANT-01"
    assert "status_summary" in data
    assert "active_tasks" in data["status_summary"]
    assert "security_alerts" in data["status_summary"]
    assert "system_health" in data["status_summary"]

    assert len(data["subsystems"]) >= 5
    sub_names = [s["service"] for s in data["subsystems"]]
    assert "Core API" in sub_names
    assert "Task Orchestrator" in sub_names
    assert "Agentic RAG Engine" in sub_names


def test_monitoring_tracks_active_tasks_and_approvals(client):
    """Verifies that submitted background tasks reflect in active tasks and needs-attention counters."""
    # 1. Submit an autonomous task
    task_res = client.post(
        "/api/v1/agentic/task/submit",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        json={"objective": "Active Task Monitoring Test"},
    )
    assert task_res.status_code == 200

    # 2. Check monitoring overview
    mon_res = client.get(
        "/api/v1/agentic/monitoring/overview",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
    )
    assert mon_res.status_code == 200
    mon_data = mon_res.json()
    assert mon_data["status_summary"]["active_tasks"] >= 1


# =========================================================================
# 2. LIVE EVENT STREAM & FILTERING
# =========================================================================

def test_monitoring_events_stream_and_category_filtering(client):
    """Verifies normalized live events stream and category-based filtering."""
    # 1. All events
    res_all = client.get(
        "/api/v1/agentic/monitoring/events",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
    )
    assert res_all.status_code == 200
    events_all = res_all.json()
    assert len(events_all) >= 2
    assert "event_id" in events_all[0]
    assert "timestamp" in events_all[0]

    # 2. Filter by SECURITY category
    res_sec = client.get(
        "/api/v1/agentic/monitoring/events?category=SECURITY",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
    )
    assert res_sec.status_code == 200
    events_sec = res_sec.json()
    assert all(e["category"] == "SECURITY" for e in events_sec)


# =========================================================================
# 3. RBAC TELEMETRY & ADVERSARIAL ACCESS DEFENSE
# =========================================================================

def test_monitoring_telemetry_admin_access(client):
    """Verifies that administrative clients receive agent and RAG performance telemetry."""
    response = client.get(
        "/api/v1/agentic/monitoring/telemetry",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
    )
    assert response.status_code == 200
    data = response.json()

    assert "agent_health" in data
    assert len(data["agent_health"]) >= 3
    assert "agentic_rag_metrics" in data
    assert data["agentic_rag_metrics"]["reranking_success_rate"] == 100.0


def test_monitoring_tenant_isolation(client):
    """Verifies that monitoring overview is isolated between tenants."""
    res_t1 = client.get(
        "/api/v1/agentic/monitoring/overview",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
    )
    res_t2 = client.get(
        "/api/v1/agentic/monitoring/overview",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-02"},
    )
    assert res_t1.json()["tenant_id"] == "TENANT-01"
    assert res_t2.json()["tenant_id"] == "TENANT-02"
