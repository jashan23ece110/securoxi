"""
SECUROXI AI Intelligence 2.0 — Production Feedback & Controlled Adaptive Improvement Models
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time
import uuid
from securoxi.orchestrator.feedback.types import (
    FeedbackCategory,
    FeedbackSource,
    FeedbackValidationState,
    FeedbackSeverity,
    ImprovementStatus,
)


@dataclass
class FeedbackEvent:
    """Strongly typed record of production user/analyst/incident feedback."""
    feedback_id: str = field(default_factory=lambda: f"FB-{uuid.uuid4().hex[:8].upper()}")
    tenant_id: str = "TENANT-DEFAULT"
    actor: str = "USER"
    task_id: Optional[str] = None
    run_id: Optional[str] = None
    source: FeedbackSource = FeedbackSource.USER
    category: FeedbackCategory = FeedbackCategory.INCORRECT_RESULT
    severity: FeedbackSeverity = FeedbackSeverity.MEDIUM
    affected_component: str = "ORCHESTRATOR"
    comment: str = ""
    references: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    validation_state: FeedbackValidationState = FeedbackValidationState.RECEIVED
    validation_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            "tenant_id": self.tenant_id,
            "actor": self.actor,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "source": self.source.value,
            "category": self.category.value,
            "severity": self.severity.value,
            "affected_component": self.affected_component,
            "comment": self.comment,
            "references": self.references,
            "timestamp": self.timestamp,
            "validation_state": self.validation_state.value,
            "validation_notes": self.validation_notes,
        }


@dataclass
class FeedbackCluster:
    """Represents a grouped cluster of similar validated feedback events."""
    cluster_id: str = field(default_factory=lambda: f"CLUST-{uuid.uuid4().hex[:8].upper()}")
    category: FeedbackCategory = FeedbackCategory.INCORRECT_RESULT
    affected_component: str = "ORCHESTRATOR"
    feedback_ids: List[str] = field(default_factory=list)
    frequency: int = 1
    root_cause_summary: str = ""
    severity: FeedbackSeverity = FeedbackSeverity.MEDIUM


@dataclass
class ImprovementCandidate:
    """Represents a proposed versioned improvement requiring evaluation and governance approval."""
    candidate_id: str = field(default_factory=lambda: f"IMP-{uuid.uuid4().hex[:8].upper()}")
    cluster_id: Optional[str] = None
    affected_component: str = "ORCHESTRATOR"
    problem_statement: str = ""
    proposed_change: str = ""
    expected_benefit: str = ""
    status: ImprovementStatus = ImprovementStatus.PROPOSED
    evaluation_run_id: Optional[str] = None
    approved_by: Optional[str] = None
    approval_timestamp: Optional[float] = None
    release_version: Optional[str] = None
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "cluster_id": self.cluster_id,
            "affected_component": self.affected_component,
            "problem_statement": self.problem_statement,
            "proposed_change": self.proposed_change,
            "expected_benefit": self.expected_benefit,
            "status": self.status.value,
            "evaluation_run_id": self.evaluation_run_id,
            "approved_by": self.approved_by,
            "approval_timestamp": self.approval_timestamp,
            "release_version": self.release_version,
            "created_at": self.created_at,
        }
