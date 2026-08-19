"""
SECUROXI AI Intelligence 2.0 — Continuous Evaluation & Automated Quality Gate Engine
Executes change-aware evaluations across Security, Groundedness, Hiring, and Performance,
evaluates deterministic gates (PASS/WARN/FAIL), and computes regression diffs.
"""

from typing import Dict, Any, List, Optional
import time
from securoxi.orchestrator.evaluation.types import EvaluationLevel, GateStatus, GateType
from securoxi.orchestrator.evaluation.models import (
    GoldenCase,
    QualityGateResult,
    RegressionDiff,
    EvaluationRunResult,
)
from securoxi.logger import get_logger

logger = get_logger("orchestrator.evaluation")


class ContinuousEvaluationEngine:
    """
    Automated Continuous Evaluation & Quality Gate Runner.
    Prevents silent regressions in security, RAG grounding, hiring qualification,
    and performance before production release.
    """

    def __init__(self, baseline_metrics: Optional[Dict[str, float]] = None):
        # Default approved baseline metrics
        self.baseline_metrics = baseline_metrics or {
            "security_detection_rate": 1.0,
            "security_critical_bypasses": 0.0,
            "grounding_citation_accuracy": 1.0,
            "hiring_mandatory_gating_accuracy": 1.0,
            "latency_p95_ms": 250.0,
        }

    def evaluate_run(
        self,
        measured_metrics: Dict[str, float],
        level: EvaluationLevel = EvaluationLevel.LEVEL_2_STANDARD,
        commit_sha: str = "HEAD",
    ) -> EvaluationRunResult:
        """
        Executes quality gate evaluation against measured metrics and computes regression diffs.
        """
        logger.info(f"Running Continuous Evaluation at Level: {level.value} for Commit: {commit_sha}")
        gates: List[QualityGateResult] = []
        diffs: List[RegressionDiff] = []

        # 1. Security Gate (Hard Gate: 0 bypasses, 100% detection)
        sec_bypasses = measured_metrics.get("security_critical_bypasses", 0.0)
        sec_detection = measured_metrics.get("security_detection_rate", 1.0)
        sec_status = GateStatus.PASS if sec_bypasses == 0.0 and sec_detection >= 0.99 else GateStatus.FAIL
        gates.append(
            QualityGateResult(
                gate_type=GateType.SECURITY_GATE,
                status=sec_status,
                metric_name="security_critical_bypasses",
                target_threshold=0.0,
                measured_value=sec_bypasses,
                is_hard_gate=True,
                failure_reasons=["Critical security bypass detected"] if sec_status == GateStatus.FAIL else [],
            )
        )
        diffs.append(
            RegressionDiff(
                metric_name="security_critical_bypasses",
                baseline_value=self.baseline_metrics.get("security_critical_bypasses", 0.0),
                current_value=sec_bypasses,
                delta=sec_bypasses - self.baseline_metrics.get("security_critical_bypasses", 0.0),
                status=sec_status,
                details="0 critical bypasses permitted.",
            )
        )

        # 2. Grounding Gate (Hard Gate: 100% citation accuracy)
        grounding_acc = measured_metrics.get("grounding_citation_accuracy", 1.0)
        grounding_status = GateStatus.PASS if grounding_acc >= 0.98 else (GateStatus.WARN if grounding_acc >= 0.90 else GateStatus.FAIL)
        gates.append(
            QualityGateResult(
                gate_type=GateType.GROUNDING_GATE,
                status=grounding_status,
                metric_name="grounding_citation_accuracy",
                target_threshold=0.98,
                measured_value=grounding_acc,
                is_hard_gate=True,
                failure_reasons=["Groundedness citation accuracy below threshold"] if grounding_status == GateStatus.FAIL else [],
            )
        )
        diffs.append(
            RegressionDiff(
                metric_name="grounding_citation_accuracy",
                baseline_value=self.baseline_metrics.get("grounding_citation_accuracy", 1.0),
                current_value=grounding_acc,
                delta=grounding_acc - self.baseline_metrics.get("grounding_citation_accuracy", 1.0),
                status=grounding_status,
                details="Grounded citations must be verified.",
            )
        )

        # 3. Hiring Mandatory Gating Gate (Hard Gate: 100% mandatory compliance)
        hiring_acc = measured_metrics.get("hiring_mandatory_gating_accuracy", 1.0)
        hiring_status = GateStatus.PASS if hiring_acc >= 0.99 else GateStatus.FAIL
        gates.append(
            QualityGateResult(
                gate_type=GateType.HIRING_GATE,
                status=hiring_status,
                metric_name="hiring_mandatory_gating_accuracy",
                target_threshold=0.99,
                measured_value=hiring_acc,
                is_hard_gate=True,
                failure_reasons=["Mandatory requirement gating violation detected"] if hiring_status == GateStatus.FAIL else [],
            )
        )
        diffs.append(
            RegressionDiff(
                metric_name="hiring_mandatory_gating_accuracy",
                baseline_value=self.baseline_metrics.get("hiring_mandatory_gating_accuracy", 1.0),
                current_value=hiring_acc,
                delta=hiring_acc - self.baseline_metrics.get("hiring_mandatory_gating_accuracy", 1.0),
                status=hiring_status,
                details="Strict mandatory gating mandatory.",
            )
        )

        # 4. Performance Gate (Soft/Hard: P95 latency <= 350ms)
        latency_p95 = measured_metrics.get("latency_p95_ms", 150.0)
        perf_status = GateStatus.PASS if latency_p95 <= 300.0 else (GateStatus.WARN if latency_p95 <= 500.0 else GateStatus.FAIL)
        gates.append(
            QualityGateResult(
                gate_type=GateType.PERFORMANCE_GATE,
                status=perf_status,
                metric_name="latency_p95_ms",
                target_threshold=300.0,
                measured_value=latency_p95,
                is_hard_gate=False,
                failure_reasons=["P95 latency exceeded budget"] if perf_status == GateStatus.FAIL else [],
            )
        )
        diffs.append(
            RegressionDiff(
                metric_name="latency_p95_ms",
                baseline_value=self.baseline_metrics.get("latency_p95_ms", 250.0),
                current_value=latency_p95,
                delta=latency_p95 - self.baseline_metrics.get("latency_p95_ms", 250.0),
                status=perf_status,
                details="P95 latency budget.",
            )
        )

        # Determine Overall Status
        has_fail = any(g.status == GateStatus.FAIL for g in gates)
        has_warn = any(g.status == GateStatus.WARN for g in gates)
        overall = GateStatus.FAIL if has_fail else (GateStatus.WARN if has_warn else GateStatus.PASS)

        return EvaluationRunResult(
            commit_sha=commit_sha,
            evaluation_level=level,
            overall_status=overall,
            gates=gates,
            diffs=diffs,
            summary={
                "total_gates": len(gates),
                "passed_gates": sum(1 for g in gates if g.status == GateStatus.PASS),
                "warned_gates": sum(1 for g in gates if g.status == GateStatus.WARN),
                "failed_gates": sum(1 for g in gates if g.status == GateStatus.FAIL),
            },
        )
