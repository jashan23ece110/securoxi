"""
SECUROXI AI Intelligence 2.0 — Autonomous Platform Operations Test Suite (Phase 9 Stage 59)
Validates platform health telemetry ingestion, anomaly detection, root-cause diagnosis,
governed remediation execution, loop protection, and operational kill switches.
"""

import pytest
from securoxi.enterprise.operations import (
    AutonomousPlatformOperationsEngine,
    RemediationActionType,
    RemediationRisk,
    ServiceHealthStatus,
)


# =========================================================================
# 1. HEALTH INGESTION, ANOMALY DETECTION & ROOT-CAUSE DIAGNOSIS
# =========================================================================

def test_health_monitoring_and_anomaly_detection():
    """Verifies that degraded telemetry generates anomalies and evidence-backed diagnoses."""
    ops = AutonomousPlatformOperationsEngine()

    # 1. Ingest Normal Telemetry -> HEALTHY
    h_normal = ops.ingest_health("core_api", latency_p95_ms=110.0, error_rate=0.0, queue_depth=10)
    assert h_normal.status == ServiceHealthStatus.HEALTHY
    assert len(ops.detect_anomalies()) == 0

    # 2. Ingest Degraded Telemetry (High Latency & Queue Saturation) -> DEGRADED
    h_degraded = ops.ingest_health("search_index", latency_p95_ms=750.0, error_rate=0.08, queue_depth=2500)
    assert h_degraded.status == ServiceHealthStatus.DEGRADED

    # Detect Anomalies
    anomalies = ops.detect_anomalies()
    assert len(anomalies) == 1
    anom = anomalies[0]
    assert anom.service_name == "search_index"
    assert "latency" in anom.symptom.lower()

    # Diagnose Root Cause
    hyp = ops.diagnose_anomaly(anom.anomaly_id)
    assert hyp is not None
    assert hyp.service_name == "search_index"
    assert hyp.confidence > 0.8


# =========================================================================
# 2. SAFE AUTO-REMEDIATION & RECOVERY VERIFICATION
# =========================================================================

def test_safe_auto_remediation():
    """Verifies low-risk auto-remediation executes and restores service health to HEALTHY."""
    ops = AutonomousPlatformOperationsEngine()

    ops.ingest_health("cache_service", latency_p95_ms=600.0, queue_depth=1200)
    anom = ops.detect_anomalies()[0]

    # Propose LOW_SAFE_AUTO remediation (e.g., CLEAR_SAFE_CACHE)
    prop = ops.propose_remediation(
        anomaly_id=anom.anomaly_id,
        action_type=RemediationActionType.CLEAR_SAFE_CACHE,
        risk_level=RemediationRisk.LOW_SAFE_AUTO,
    )

    # Execute without explicit human approval -> Allowed for LOW_SAFE_AUTO
    res = ops.execute_remediation(prop.proposal_id)
    assert res["success"] is True
    assert res["status"] == "SUCCESS"

    # Verify service health restored to HEALTHY
    assert ops._services["cache_service"].status == ServiceHealthStatus.HEALTHY
    assert ops._services["cache_service"].latency_p95_ms < 500.0


# =========================================================================
# 3. APPROVAL GATES, LOOP PROTECTION & KILL SWITCH
# =========================================================================

def test_remediation_approval_gates_loop_limit_and_kill_switch():
    """Verifies approval requirements for moderate/high risk actions, loop limits, and kill switches."""
    ops = AutonomousPlatformOperationsEngine()

    ops.ingest_health("db_replica", latency_p95_ms=800.0)
    anom = ops.detect_anomalies()[0]

    # 1. Propose Moderate Risk Action (e.g., FAILOVER_PROVIDER)
    prop = ops.propose_remediation(
        anomaly_id=anom.anomaly_id,
        action_type=RemediationActionType.FAILOVER_PROVIDER,
        risk_level=RemediationRisk.MODERATE_APPROVAL_REQUIRED,
    )

    # Unapproved Execution -> APPROVAL_REQUIRED
    res_unapproved = ops.execute_remediation(prop.proposal_id)
    assert res_unapproved["success"] is False
    assert res_unapproved["error"] == "APPROVAL_REQUIRED"

    # Approved Execution -> SUCCESS
    res_approved = ops.execute_remediation(prop.proposal_id, approved_by="SRE_LEAD")
    assert res_approved["success"] is True

    # 2. Remediation Loop Limit Protection (Max 3 attempts per service)
    for _ in range(2):
        p = ops.propose_remediation(anom.anomaly_id, RemediationActionType.RETRY_TASK, RemediationRisk.LOW_SAFE_AUTO)
        ops.execute_remediation(p.proposal_id)

    # 4th attempt -> REMEDIATION_LOOP_LIMIT_EXCEEDED
    p_fourth = ops.propose_remediation(anom.anomaly_id, RemediationActionType.RETRY_TASK, RemediationRisk.LOW_SAFE_AUTO)
    res_loop = ops.execute_remediation(p_fourth.proposal_id)
    assert res_loop["success"] is False
    assert res_loop["error"] == "REMEDIATION_LOOP_LIMIT_EXCEEDED"

    # 3. Operational Kill Switch -> BLOCKS ALL
    ops.set_kill_switch(True)
    p_kill = ops.propose_remediation("ANOM-OTHER", RemediationActionType.CLEAR_SAFE_CACHE, RemediationRisk.LOW_SAFE_AUTO)
    res_kill = ops.execute_remediation(p_kill.proposal_id)
    assert res_kill["success"] is False
    assert res_kill["error"] == "OPERATIONS_KILL_SWITCH_ACTIVE"
