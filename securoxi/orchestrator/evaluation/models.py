"""
SECUROXI AI Intelligence 2.0 — Continuous Evaluation & Quality Gate Models
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time
import uuid
from securoxi.orchestrator.evaluation.types import EvaluationLevel, GateStatus, GateType


@dataclass
class GoldenCase:
    """Represents a curated, human-verified ground-truth test case."""
    case_id: str
    category: str
    input_payload: Dict[str, Any]
    expected_output: Dict[str, Any]
    expected_security_verdict: str = "SAFE"
    is_hard_gate: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityGateResult:
    """Result of an individual deterministic quality gate evaluation."""
    gate_type: GateType
    status: GateStatus
    metric_name: str
    target_threshold: float
    measured_value: float
    is_hard_gate: bool = True
    failure_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_type": self.gate_type.value,
            "status": self.status.value,
            "metric_name": self.metric_name,
            "target_threshold": self.target_threshold,
            "measured_value": self.measured_value,
            "is_hard_gate": self.is_hard_gate,
            "failure_reasons": self.failure_reasons,
        }


@dataclass
class RegressionDiff:
    """Concise regression diff comparing baseline vs current measured performance."""
    metric_name: str
    baseline_value: float
    current_value: float
    delta: float
    status: GateStatus
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "baseline_value": self.baseline_value,
            "current_value": self.current_value,
            "delta": round(self.delta, 4),
            "status": self.status.value,
            "details": self.details,
        }


@dataclass
class EvaluationRunResult:
    """Top-level immutable artifact containing end-to-end evaluation run results."""
    run_id: str = field(default_factory=lambda: f"EVAL-{uuid.uuid4().hex[:8].upper()}")
    commit_sha: str = "HEAD"
    evaluation_level: EvaluationLevel = EvaluationLevel.LEVEL_2_STANDARD
    timestamp: float = field(default_factory=time.time)
    overall_status: GateStatus = GateStatus.PASS
    gates: List[QualityGateResult] = field(default_factory=list)
    diffs: List[RegressionDiff] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "commit_sha": self.commit_sha,
            "evaluation_level": self.evaluation_level.value,
            "timestamp": self.timestamp,
            "overall_status": self.overall_status.value,
            "gates": [g.to_dict() for g in self.gates],
            "diffs": [d.to_dict() for d in self.diffs],
            "summary": self.summary,
        }
