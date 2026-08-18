"""
SECUROXI AI Intelligence 2.0 — Planning Data Models
Defines data structures for Structured Conditions, Resolved Entities, Plan Node Specifications,
Plans, and Plan Version Records.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from securoxi.orchestrator.planning.types import (
    TaskIntent,
    ConditionType,
    ConstraintPriorityLevel,
    PlanConfidence,
    PlanningStatus,
    ReplanReason,
)
from securoxi.orchestrator.types import NodeType, ExecutionType, TrustLevel


@dataclass
class StructuredCondition:
    """A strongly typed condition or constraint parsed from user intent or security rules."""
    condition_id: str = field(default_factory=lambda: f"COND-{uuid.uuid4().hex[:8].upper()}")
    raw_text: str = ""
    normalized_field: str = ""        # e.g., "min_experience_years", "required_skills", "security_status"
    operator: str = "=="              # "==", ">=", "<=", "IN", "NOT_IN", "CONTAINS"
    value: Any = None                 # e.g., 5, ["Kubernetes", "AWS"], ["SAFE", "SUSPICIOUS"]
    condition_type: ConditionType = ConditionType.MANDATORY
    priority_level: ConstraintPriorityLevel = ConstraintPriorityLevel.USER_MANDATORY
    is_immutable: bool = False        # True for System Security Constraints

    def to_dict(self) -> Dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "raw_text": self.raw_text,
            "normalized_field": self.normalized_field,
            "operator": self.operator,
            "value": self.value,
            "condition_type": self.condition_type.value,
            "priority_level": self.priority_level.value,
            "is_immutable": self.is_immutable,
        }


@dataclass
class ResolvedEntity:
    """An entity resolved and authorized against backend data systems."""
    entity_id: str = field(default_factory=lambda: f"ENT-{uuid.uuid4().hex[:8].upper()}")
    entity_type: str = "DOCUMENT"     # "FOLDER", "DOCUMENT", "CANDIDATE", "JOB_DESCRIPTION", "COLLECTION", "TENANT"
    raw_name: str = ""
    resolved_id: str = ""
    is_authorized: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "raw_name": self.raw_name,
            "resolved_id": self.resolved_id,
            "is_authorized": self.is_authorized,
            "metadata": self.metadata,
        }


@dataclass
class ClarificationRequest:
    """A minimal, actionable question presented to the user to resolve ambiguity."""
    question_id: str = field(default_factory=lambda: f"CLAR-{uuid.uuid4().hex[:6].upper()}")
    target_field: str = ""
    question_text: str = ""
    options: List[str] = field(default_factory=list)
    default_fallback: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "target_field": self.target_field,
            "question_text": self.question_text,
            "options": self.options,
            "default_fallback": self.default_fallback,
        }


@dataclass
class PlanNodeSpec:
    """Declarative specification for a node to be instantiated into the ExecutionDAG."""
    node_id: str = field(default_factory=lambda: f"PNODE-{uuid.uuid4().hex[:8].upper()}")
    name: str = ""
    node_type: NodeType = NodeType.TRANSFORM
    description: str = ""
    tool_id: Optional[str] = None
    agent_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    input_bindings: Dict[str, Any] = field(default_factory=dict)
    execution_type: ExecutionType = ExecutionType.DETERMINISTIC
    trust_level: TrustLevel = TrustLevel.LOW_RISK
    timeout_sec: float = 60.0
    is_parallelizable: bool = False
    condition_expr: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "node_type": self.node_type.value,
            "description": self.description,
            "tool_id": self.tool_id,
            "agent_id": self.agent_id,
            "dependencies": self.dependencies,
            "input_bindings": self.input_bindings,
            "execution_type": self.execution_type.value,
            "trust_level": self.trust_level.value,
            "timeout_sec": self.timeout_sec,
            "is_parallelizable": self.is_parallelizable,
            "condition_expr": self.condition_expr,
        }


@dataclass
class TaskUnderstanding:
    """Structured understanding derived from user intent."""
    raw_prompt: str = ""
    primary_intent: TaskIntent = TaskIntent.DOCUMENT_SCAN
    objective_summary: str = ""
    requested_output_format: str = "SUMMARY"  # "RANKED_LIST", "SUMMARY", "METRICS", "INCIDENT_REPORT"
    target_count: Optional[int] = None        # e.g., 20 candidates
    entities: List[ResolvedEntity] = field(default_factory=list)
    conditions: List[StructuredCondition] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    confidence: PlanConfidence = PlanConfidence.HIGH_CONFIDENCE
    confidence_reason: str = "Clear intent and fully resolved entities."
    clarifications: List[ClarificationRequest] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_prompt": self.raw_prompt,
            "primary_intent": self.primary_intent.value,
            "objective_summary": self.objective_summary,
            "requested_output_format": self.requested_output_format,
            "target_count": self.target_count,
            "entities": [e.to_dict() for e in self.entities],
            "conditions": [c.to_dict() for c in self.conditions],
            "assumptions": self.assumptions,
            "confidence": self.confidence.value,
            "confidence_reason": self.confidence_reason,
            "clarifications": [q.to_dict() for q in self.clarifications],
        }


@dataclass
class Plan:
    """Structured, versioned execution plan produced by the planner."""
    plan_id: str = field(default_factory=lambda: f"PLAN-{uuid.uuid4().hex[:10].upper()}")
    task_id: str = ""
    version: int = 1
    status: PlanningStatus = PlanningStatus.DRAFT
    intent: TaskIntent = TaskIntent.DOCUMENT_SCAN
    objective: str = ""
    understanding: Optional[TaskUnderstanding] = None
    nodes: List[PlanNodeSpec] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    estimated_cost_usd: float = 0.05
    estimated_runtime_sec: float = 30.0
    summary_explanation: str = ""
    created_at: float = field(default_factory=time.time)
    created_by: str = "PLANNER_ENGINE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "task_id": self.task_id,
            "version": self.version,
            "status": self.status.value,
            "intent": self.intent.value,
            "objective": self.objective,
            "understanding": self.understanding.to_dict() if self.understanding else None,
            "nodes": [n.to_dict() for n in self.nodes],
            "dependencies": self.dependencies,
            "estimated_cost_usd": self.estimated_cost_usd,
            "estimated_runtime_sec": self.estimated_runtime_sec,
            "summary_explanation": self.summary_explanation,
            "created_at": self.created_at,
            "created_by": self.created_by,
        }


@dataclass
class PlanVersionRecord:
    """Audit history of plan revisions and adaptive replanning."""
    record_id: str = field(default_factory=lambda: f"PVER-{uuid.uuid4().hex[:8].upper()}")
    plan_id: str = ""
    version: int = 1
    replan_reason: ReplanReason = ReplanReason.INPUT_CHANGED
    details: str = ""
    created_at: float = field(default_factory=time.time)
    plan_snapshot: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "plan_id": self.plan_id,
            "version": self.version,
            "replan_reason": self.replan_reason.value,
            "details": self.details,
            "created_at": self.created_at,
            "plan_snapshot": self.plan_snapshot,
        }
