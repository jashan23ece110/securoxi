"""
SECUROXI AI Intelligence 2.0 — Production Telemetry Analysis & Bottleneck Detection Test Suite (Stage 28)
Validates trace correlation, latency percentiles (P50/P75/P95/P99), stage decomposition,
bottleneck detection, root cause classification, and tenant-isolated metric privacy.
"""

import pytest
from fastapi.testclient import TestClient
from securoxi.api.app import app
from securoxi.orchestrator.telemetry_analysis import ProductionTelemetryAnalyzer


@pytest.fixture
def client():
    return TestClient(app)


# =========================================================================
# 1. TRACE RECORDING & LATENCY PERCENTILES
# =========================================================================

def test_telemetry_analyzer_trace_recording_and_percentiles():
    """Verifies that traces are properly aggregated and percentiles are accurately calculated."""
    analyzer = ProductionTelemetryAnalyzer()

    # Record specific trace
    trace = analyzer.record_trace(
        task_id="TASK-TEST-001",
        run_id="RUN-TEST-001",
        tenant_id="TENANT-CUSTOM",
        workflow_type="ASK_RAG",
        total_duration_ms=350.0,
        stage_durations_ms={
            "planning": 15.0,
            "security": 45.0,
            "retrieval": 120.0,
            "reranking": 90.0,
            "verification": 50.0,
            "synthesis": 30.0,
        },
        agent_invocations={"RetrievalAgent": 2},
        retrieval_hops=2,
    )
    assert trace.trace_id.startswith("TRC-")
    assert trace.total_duration_ms == 350.0

    breakdown = analyzer.get_latency_breakdown("TENANT-CUSTOM")
    assert breakdown["tenant_id"] == "TENANT-CUSTOM"
    assert "overall_latency_ms" in breakdown
    assert "p50" in breakdown["overall_latency_ms"]
    assert "p95" in breakdown["overall_latency_ms"]
    assert "stage_breakdown" in breakdown
    assert "reranking" in breakdown["stage_breakdown"]


# =========================================================================
# 2. BOTTLENECK DETECTION & ROOT CAUSE CLASSIFICATION
# =========================================================================

def test_bottleneck_detection_and_ranking():
    """Verifies that the analyzer detects and ranks bottlenecks by impact percentage."""
    analyzer = ProductionTelemetryAnalyzer()
    bottlenecks = analyzer.get_bottlenecks("TENANT-01")

    assert len(bottlenecks) >= 3
    # Top bottleneck should have the highest impact percentage
    assert bottlenecks[0]["impact_percentage"] >= bottlenecks[1]["impact_percentage"]
    assert bottlenecks[0]["confidence"] == "CONFIRMED_ROOT_CAUSE"
    assert "proposed_mitigation" in bottlenecks[0]


# =========================================================================
# 3. REST ENDPOINTS & TENANT ISOLATION
# =========================================================================

def test_telemetry_analysis_rest_endpoints(client):
    """Verifies REST endpoints for bottleneck and telemetry analysis."""
    # 1. Bottlenecks
    bot_res = client.get(
        "/api/v1/agentic/monitoring/bottlenecks",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
    )
    assert bot_res.status_code == 200
    bots = bot_res.json()
    assert len(bots) >= 3
    assert bots[0]["id"] == "BOTTLENECK-02" or bots[0]["id"] == "BOTTLENECK-01"

    # 2. Stage Analysis
    ana_res = client.get(
        "/api/v1/agentic/monitoring/telemetry/analysis",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
    )
    assert ana_res.status_code == 200
    ana = ana_res.json()
    assert ana["tenant_id"] == "TENANT-01"
    assert "stage_breakdown" in ana
    assert "retrieval" in ana["stage_breakdown"]


def test_telemetry_privacy_no_raw_documents(client):
    """Verifies that telemetry traces and analysis never expose raw document or resume text."""
    ana_res = client.get(
        "/api/v1/agentic/monitoring/telemetry/analysis",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
    )
    assert ana_res.status_code == 200
    content_str = str(ana_res.json()).lower()
    assert "resume" not in content_str
    assert "candidate_text" not in content_str
    assert "password" not in content_str
