"""
SECUROXI AI Intelligence 2.0 — Orchestrator Data Models
Defines strongly-typed data structures for Tasks, Runs, Budgets, and Human Approval Requests.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from securoxi.orchestrator.types import (
    TaskPriority,
    TaskStatus,
    RunState,
    SecurityClassification,
    ApprovalStatus,
)


@dataclass
class TaskBudget:
    """Execution constraints and resource budgets for a task and its runs."""
    max_steps: int = 50
    max_tool_calls: int = 100
    max_runtime_sec: float = 300.0
    max_parallel_branches: int = 10
    max_retries: int = 3
    max_output_bytes: int = 10 * 1024 * 1024  # 10 MB
    max_tokens: Optional[int] = 100000
    max_cost_usd: Optional[float] = 5.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_steps": self.max_steps,
            "max_tool_calls": self.max_tool_calls,
            "max_runtime_sec": self.max_runtime_sec,
            "max_parallel_branches": self.max_parallel_branches,
            "max_retries": self.max_retries,
            "max_output_bytes": self.max_output_bytes,
            "max_tokens": self.max_tokens,
            "max_cost_usd": self.max_cost_usd,
        }


@dataclass
class Task:
    """High-level declaration of work to be accomplished."""
    task_id: str = field(default_factory=lambda: f"TASK-{uuid.uuid4().hex[:10].upper()}")
    tenant_id: str = "TENANT-DEFAULT"
    actor_id: str = "SYSTEM"
    objective: str = ""
    constraints: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    requested_output_schema: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    deadline: Optional[float] = None
    budget: TaskBudget = field(default_factory=TaskBudget)
    security_classification: SecurityClassification = SecurityClassification.INTERNAL
    requires_approval: bool = False
    parent_task_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "objective": self.objective,
            "constraints": self.constraints,
            "context": self.context,
            "requested_output_schema": self.requested_output_schema,
            "priority": self.priority.value,
            "deadline": self.deadline,
            "budget": self.budget.to_dict(),
            "security_classification": self.security_classification.value,
            "requires_approval": self.requires_approval,
            "parent_task_id": self.parent_task_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


@dataclass
class RunAttempt:
    """Record of an individual execution attempt of a run."""
    attempt_number: int = 1
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    status: RunState = RunState.RUNNING
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attempt_number": self.attempt_number,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "status": self.status.value,
            "error": self.error,
        }


@dataclass
class Run:
    """Instance of an execution attempt for a specific Task."""
    run_id: str = field(default_factory=lambda: f"RUN-{uuid.uuid4().hex[:10].upper()}")
    task_id: str = ""
    tenant_id: str = "TENANT-DEFAULT"
    actor_id: str = "SYSTEM"
    state: RunState = RunState.CREATED
    attempts: List[RunAttempt] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    total_steps_executed: int = 0
    total_tool_calls_executed: int = 0
    total_runtime_ms: float = 0.0
    tokens_consumed: int = 0
    estimated_cost_usd: float = 0.0
    error: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "task_id": self.task_id,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "state": self.state.value,
            "attempts": [a.to_dict() for a in self.attempts],
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_steps_executed": self.total_steps_executed,
            "total_tool_calls_executed": self.total_tool_calls_executed,
            "total_runtime_ms": self.total_runtime_ms,
            "tokens_consumed": self.tokens_consumed,
            "estimated_cost_usd": self.estimated_cost_usd,
            "error": self.error,
            "result": self.result,
            "metadata": self.metadata,
        }


@dataclass
class ApprovalRequest:
    """Audit record for human approval gates."""
    approval_id: str = field(default_factory=lambda: f"APPR-{uuid.uuid4().hex[:8].upper()}")
    run_id: str = ""
    node_id: str = ""
    tenant_id: str = "TENANT-DEFAULT"
    actor_id: str = ""
    action_summary: str = ""
    proposed_payload: Dict[str, Any] = field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    decided_by: Optional[str] = None
    decided_at: Optional[float] = None
    reason: Optional[str] = None
    timeout_sec: float = 3600.0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "run_id": self.run_id,
            "node_id": self.node_id,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "action_summary": self.action_summary,
            "proposed_payload": self.proposed_payload,
            "status": self.status.value,
            "decided_by": self.decided_by,
            "decided_at": self.decided_at,
            "reason": self.reason,
            "timeout_sec": self.timeout_sec,
            "created_at": self.created_at,
        }
