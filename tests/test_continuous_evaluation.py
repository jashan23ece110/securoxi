"""
SECUROXI AI Intelligence 2.0 — Continuous Evaluation & Automated Quality Gates Test Suite (Stage 33)
Validates automated quality gate execution, hard security gate blocking, regression diff calculation,
and continuous evaluation reporting across Security, Groundedness, Hiring, and Performance.
"""

import pytest
from securoxi.orchestrator.evaluation import (
    ContinuousEvaluationEngine,
    EvaluationLevel,
    GateStatus,
    GateType,
)


# =========================================================================
# 1. PASSING CONTINUOUS EVALUATION RUN
# =========================================================================

def test_continuous_evaluation_pass():
    """Verifies that when all metrics meet or exceed thresholds, evaluation passes."""
    engine = ContinuousEvaluationEngine()

    measured = {
        "security_critical_bypasses": 0.0,
        "security_detection_rate": 1.0,
        "grounding_citation_accuracy": 1.0,
        "hiring_mandatory_gating_accuracy": 1.0,
        "latency_p95_ms": 180.0,
    }

    result = engine.evaluate_run(measured, level=EvaluationLevel.LEVEL_2_STANDARD, commit_sha="COMMIT-ABC")
    assert result.overall_status == GateStatus.PASS
    assert result.summary["failed_gates"] == 0
    assert len(result.gates) == 4
    assert len(result.diffs) == 4


# =========================================================================
# 2. HARD SECURITY GATE BLOCKING (ZERO BYPASS INVARIANT)
# =========================================================================

def test_hard_security_gate_blocks_release():
    """Verifies that even a single critical security bypass results in overall FAIL."""
    engine = ContinuousEvaluationEngine()

    measured_failing = {
        "security_critical_bypasses": 1.0,  # Security bypass detected!
        "security_detection_rate": 0.95,
        "grounding_citation_accuracy": 1.0,
        "hiring_mandatory_gating_accuracy": 1.0,
        "latency_p95_ms": 120.0,
    }

    result = engine.evaluate_run(measured_failing, level=EvaluationLevel.LEVEL_3_DEEP, commit_sha="COMMIT-FAIL")
    assert result.overall_status == GateStatus.FAIL
    sec_gate = next(g for g in result.gates if g.gate_type == GateType.SECURITY_GATE)
    assert sec_gate.status == GateStatus.FAIL
    assert len(sec_gate.failure_reasons) >= 1


# =========================================================================
# 3. REGRESSION DIFF TRACKING
# =========================================================================

def test_regression_diff_calculation():
    """Verifies that regression diffs correctly calculate baseline delta."""
    engine = ContinuousEvaluationEngine()

    measured = {
        "security_critical_bypasses": 0.0,
        "security_detection_rate": 1.0,
        "grounding_citation_accuracy": 1.0,
        "hiring_mandatory_gating_accuracy": 1.0,
        "latency_p95_ms": 200.0,  # 50ms faster than baseline 250ms
    }

    result = engine.evaluate_run(measured)
    lat_diff = next(d for d in result.diffs if d.metric_name == "latency_p95_ms")
    assert lat_diff.delta == -50.0
    assert lat_diff.status == GateStatus.PASS
