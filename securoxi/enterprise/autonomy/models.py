"""
SECUROXI AI Intelligence 2.0 — Controlled Autonomous Action Models (Phase 8 Stage 52)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
import time
import uuid
from securoxi.enterprise.autonomy.types import (
    AutonomyLevel,
    ActionImpactClass,
    ActionReversibility,
    ProposalStatus,
    ExecutionStatus,
)


@dataclass
class ActionProposal:
    """Strongly typed proposal for an autonomous or governed action."""
    proposal_id: str = field(default_factory=lambda: f"ACT-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-DEFAULT"
    action_type: str = "REFRESH_INDEX"
    target_resource_id: str = "RES-001"
    parameters: Dict[str, Any] = field(default_factory=dict)
    impact_class: ActionImpactClass = ActionImpactClass.LOW_IMPACT_REVERSIBLE
    reversibility: ActionReversibility = ActionReversibility.REVERSIBLE
    autonomy_level: AutonomyLevel = AutonomyLevel.L3_GUARDED_AUTONOMOUS_LOW_IMPACT
    reason: str = "Automated cache and index synchronization"
    idempotency_key: str = field(default_factory=lambda: f"IDEM-{uuid.uuid4().hex[:12]}")
    status: ProposalStatus = ProposalStatus.PROPOSED
    source_evidence_version: int = 1
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 3600)


@dataclass
class ActionOutcome:
    """Post-action verification result."""
    action_id: str = "ACT-DEFAULT"
    expected_state: str = "ACTIVE"
    observed_state: str = "ACTIVE"
    is_verified: bool = True
    verified_at: float = field(default_factory=time.time)


@dataclass
class ActionExecution:
    """Audit record of an executed action and its verification outcome."""
    execution_id: str = field(default_factory=lambda: f"EXEC-{uuid.uuid4().hex[:8].upper()}")
    proposal_id: str = "ACT-DEFAULT"
    organization_id: str = "ORG-DEFAULT"
    executed_by: str = "SYSTEM_AUTONOMOUS"
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    outcome: Optional[ActionOutcome] = None
    executed_at: float = field(default_factory=time.time)
