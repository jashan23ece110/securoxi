"""
SECUROXI AI Intelligence 2.0 — Enterprise Control Plane Models (Phase 9 Stage 54)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
import time
import uuid
from securoxi.enterprise.controlplane.types import (
    PolicyDomain,
    PolicyStatus,
    CapabilityStatus,
    EvaluationGateState,
    ControlPlaneDecision,
)


@dataclass
class PolicyDefinition:
    """Canonical declarative policy definition."""
    policy_id: str = field(default_factory=lambda: f"POL-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: Optional[str] = None  # None = Org-level policy
    domain: PolicyDomain = PolicyDomain.SECURITY
    version: int = 1
    status: PolicyStatus = PolicyStatus.ACTIVE
    rules: Dict[str, Any] = field(default_factory=dict)
    created_by: str = "SYSTEM_ADMIN"
    approved_by: Optional[str] = "GOVERNANCE_BOARD"
    created_at: float = field(default_factory=time.time)


@dataclass
class CapabilityDefinition:
    """Registered tool/agent/integration capability."""
    capability_id: str = field(default_factory=lambda: f"CAP-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    name: str = "ATS Write Connector"
    category: str = "INTEGRATION"
    required_permissions: List[str] = field(default_factory=lambda: ["ats:write"])
    allowed_autonomy_level: str = "L2_HUMAN_APPROVAL_REQUIRED"
    status: CapabilityStatus = CapabilityStatus.ENABLED
    evaluation_state: EvaluationGateState = EvaluationGateState.PASS
    version: str = "1.0.0"
    created_at: float = field(default_factory=time.time)


@dataclass
class EnterpriseDecisionContext:
    """Unified decision context capturing the active state across all specialized authorities."""
    context_id: str = field(default_factory=lambda: f"CTX-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-DEFAULT"
    actor_id: str = "USER-DEFAULT"
    policy_version: int = 1
    effective_autonomy_level: str = "L2_HUMAN_APPROVAL_REQUIRED"
    security_state: str = "SAFE"
    evaluation_state: EvaluationGateState = EvaluationGateState.PASS
    budget_remaining_pct: float = 100.0
    created_at: float = field(default_factory=time.time)


@dataclass
class ControlPlaneSnapshot:
    """Immutable snapshot of control plane state for audit and decision replay."""
    snapshot_id: str = field(default_factory=lambda: f"SNAP-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-DEFAULT"
    decision: ControlPlaneDecision = ControlPlaneDecision.ALLOW
    reason: str = "All deterministic security and policy gates passed"
    context: Optional[EnterpriseDecisionContext] = None
    created_at: float = field(default_factory=time.time)
