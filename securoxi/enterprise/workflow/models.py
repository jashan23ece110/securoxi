"""
SECUROXI AI Intelligence 2.0 — Enterprise Workflow Composer Models (Phase 9 Stage 55)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time
import uuid
from securoxi.enterprise.workflow.types import (
    WorkflowStatus,
    TriggerType,
    NodeType,
    WorkflowRiskClass,
    RunStatus,
)


@dataclass
class WorkflowNode:
    """Canonical node definition in a declarative workflow DAG."""
    node_id: str
    node_type: NodeType
    capability_name: str
    config: Dict[str, Any] = field(default_factory=dict)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    requires_approval: bool = False
    is_high_impact: bool = False


@dataclass
class WorkflowEdge:
    """Directed edge connecting nodes with optional condition predicate."""
    source_node_id: str
    target_node_id: str
    condition_expression: Optional[str] = None  # e.g., "security_state == 'SAFE'"


@dataclass
class WorkflowDefinition:
    """Immutable, versioned declarative workflow definition."""
    workflow_id: str = field(default_factory=lambda: f"WF-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-DEFAULT"
    name: str = "Candidate Screening & Security Pipeline"
    description: str = "Automated resume security scan, screening, and governed ATS stage update"
    version: int = 1
    status: WorkflowStatus = WorkflowStatus.DRAFT
    risk_class: WorkflowRiskClass = WorkflowRiskClass.LOW
    trigger_type: TriggerType = TriggerType.EVENT
    nodes: List[WorkflowNode] = field(default_factory=list)
    edges: List[WorkflowEdge] = field(default_factory=list)
    created_by: str = "WORKFLOW_ADMIN"
    approved_by: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class WorkflowRun:
    """Durable workflow execution instance."""
    run_id: str = field(default_factory=lambda: f"RUN-{uuid.uuid4().hex[:8].upper()}")
    workflow_id: str = "WF-DEFAULT"
    workflow_version: int = 1
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-DEFAULT"
    status: RunStatus = RunStatus.READY
    current_node_id: Optional[str] = None
    executed_nodes: List[str] = field(default_factory=list)
    node_outputs: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


@dataclass
class WorkflowSimulationResult:
    """Simulation run report ensuring zero live external side effects."""
    simulation_id: str = field(default_factory=lambda: f"SIM-WF-{uuid.uuid4().hex[:8].upper()}")
    workflow_id: str = "WF-DEFAULT"
    organization_id: str = "ORG-DEFAULT"
    nodes_executed: List[str] = field(default_factory=list)
    branches_taken: List[str] = field(default_factory=list)
    proposed_actions: List[str] = field(default_factory=list)
    approvals_required: List[str] = field(default_factory=list)
    is_simulation: bool = True
    simulated_at: float = field(default_factory=time.time)
