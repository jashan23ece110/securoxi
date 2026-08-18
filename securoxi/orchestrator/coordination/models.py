"""
SECUROXI AI Intelligence 2.0 — Multi-Agent Coordination Data Models
Defines strongly typed models for Agent Handoffs, Result Envelopes, Coordination Plans,
Cross-Agent Conflicts, Verification Results, and top-level Coordination Results.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import uuid
import time
from securoxi.orchestrator.coordination.types import (
    AuthorityLevel,
    HandoffStatus,
    VerificationState,
    ConflictType,
    CoordinationCompletionStatus,
)
from securoxi.orchestrator.types import TrustLevel


@dataclass
class AgentHandoff:
    """Explicit, policy-controlled contract for delegating work from one agent to another."""
    handoff_id: str = field(default_factory=lambda: f"HO-{uuid.uuid4().hex[:8].upper()}")
    source_agent_id: str = "COORDINATOR"
    target_agent_id: str = "security-agent"
    task_id: str = ""
    run_id: str = ""
    tenant_id: str = "TENANT-DEFAULT"
    purpose: str = ""
    structured_input: Dict[str, Any] = field(default_factory=dict)
    required_output_schema: str = "AgentOutput"
    trust_level: TrustLevel = TrustLevel.CONTROLLED
    provenance: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    budget_allocated: float = 1.0
    status: HandoffStatus = HandoffStatus.REQUESTED
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "handoff_id": self.handoff_id,
            "source_agent_id": self.source_agent_id,
            "target_agent_id": self.target_agent_id,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "tenant_id": self.tenant_id,
            "purpose": self.purpose,
            "structured_input": self.structured_input,
            "required_output_schema": self.required_output_schema,
            "trust_level": self.trust_level.value,
            "provenance": self.provenance,
            "constraints": self.constraints,
            "budget_allocated": self.budget_allocated,
            "status": self.status.value,
            "created_at": self.created_at,
        }


@dataclass
class AgentResultEnvelope:
    """Standardized envelope wrapping individual agent execution outputs with explicit authority."""
    envelope_id: str = field(default_factory=lambda: f"ENV-{uuid.uuid4().hex[:8].upper()}")
    agent_identity: str = ""
    agent_version: str = "1.0.0"
    status: str = "COMPLETED"
    authority_level: AuthorityLevel = AuthorityLevel.ADVISORY
    result_data: Dict[str, Any] = field(default_factory=dict)
    evidence_refs: List[str] = field(default_factory=list)
    provenance: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    verification_state: VerificationState = VerificationState.UNVERIFIED
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "envelope_id": self.envelope_id,
            "agent_identity": self.agent_identity,
            "agent_version": self.agent_version,
            "status": self.status,
            "authority_level": self.authority_level.value,
            "result_data": self.result_data,
            "evidence_refs": self.evidence_refs,
            "provenance": self.provenance,
            "warnings": self.warnings,
            "conflicts": self.conflicts,
            "verification_state": self.verification_state.value,
            "created_at": self.created_at,
        }


@dataclass
class CoordinationConflict:
    """Structured record of disagreement or contradictory findings between agents/authorities."""
    conflict_id: str = field(default_factory=lambda: f"CONF-{uuid.uuid4().hex[:8].upper()}")
    conflict_type: ConflictType = ConflictType.SECURITY_CONFLICT
    conflicting_agents: List[str] = field(default_factory=list)
    claims: Dict[str, Any] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    authority_levels: Dict[str, str] = field(default_factory=dict)
    resolved: bool = False
    resolution_method: str = "DETERMINISTIC_AUTHORITY"
    resolution_outcome: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "conflict_type": self.conflict_type.value,
            "conflicting_agents": self.conflicting_agents,
            "claims": self.claims,
            "evidence": self.evidence,
            "authority_levels": self.authority_levels,
            "resolved": self.resolved,
            "resolution_method": self.resolution_method,
            "resolution_outcome": self.resolution_outcome,
        }


@dataclass
class CoordinationStep:
    """Individual execution step within a dynamic Multi-Agent Coordination Plan."""
    step_id: str
    agent_id: str
    purpose: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    expected_outputs: List[str] = field(default_factory=list)
    authority_level: AuthorityLevel = AuthorityLevel.ADVISORY

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "agent_id": self.agent_id,
            "purpose": self.purpose,
            "inputs": self.inputs,
            "dependencies": self.dependencies,
            "expected_outputs": self.expected_outputs,
            "authority_level": self.authority_level.value,
        }


@dataclass
class CoordinationPlan:
    """Dynamic plan orchestrating participating specialized agents, dependencies, and bounds."""
    plan_id: str = field(default_factory=lambda: f"CPLAN-{uuid.uuid4().hex[:8].upper()}")
    task_id: str = ""
    tenant_id: str = "TENANT-DEFAULT"
    participating_agents: List[str] = field(default_factory=list)
    steps: List[CoordinationStep] = field(default_factory=list)
    verification_rules: List[str] = field(default_factory=list)
    fallback_behavior: str = "FAIL_SAFE_STOP"
    timeout_seconds: float = 60.0
    max_handoffs: int = 20

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "task_id": self.task_id,
            "tenant_id": self.tenant_id,
            "participating_agents": self.participating_agents,
            "steps": [s.to_dict() for s in self.steps],
            "verification_rules": self.verification_rules,
            "fallback_behavior": self.fallback_behavior,
            "timeout_seconds": self.timeout_seconds,
            "max_handoffs": self.max_handoffs,
        }


@dataclass
class VerificationResult:
    """Outcome of cross-agent and authoritative safety validation."""
    is_valid: bool = True
    verification_state: VerificationState = VerificationState.VERIFIED
    conflicts: List[CoordinationConflict] = field(default_factory=list)
    provenance_valid: bool = True
    security_cleared: bool = True
    unresolved_issues: List[str] = field(default_factory=list)
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "verification_state": self.verification_state.value,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "provenance_valid": self.provenance_valid,
            "security_cleared": self.security_cleared,
            "unresolved_issues": self.unresolved_issues,
            "details": self.details,
        }


@dataclass
class ConsensusResult:
    """Structured consensus record among advisory agents."""
    consensus_achieved: bool = True
    agreed_value: Any = None
    participating_agents: List[str] = field(default_factory=list)
    dissenting_agents: List[str] = field(default_factory=list)
    authority_level: AuthorityLevel = AuthorityLevel.SUPPORTED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "consensus_achieved": self.consensus_achieved,
            "agreed_value": self.agreed_value,
            "participating_agents": self.participating_agents,
            "dissenting_agents": self.dissenting_agents,
            "authority_level": self.authority_level.value,
        }


@dataclass
class CoordinationResult:
    """Top-level terminal result of a multi-agent coordination workflow."""
    task_id: str
    run_id: str
    tenant_id: str
    status: CoordinationCompletionStatus = CoordinationCompletionStatus.COMPLETED
    final_result: Dict[str, Any] = field(default_factory=dict)
    agent_envelopes: List[AgentResultEnvelope] = field(default_factory=list)
    conflicts: List[CoordinationConflict] = field(default_factory=list)
    verification: VerificationResult = field(default_factory=VerificationResult)
    provenance_chain: List[str] = field(default_factory=list)
    human_review_packet: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "run_id": self.run_id,
            "tenant_id": self.tenant_id,
            "status": self.status.value,
            "final_result": self.final_result,
            "agent_envelopes": [e.to_dict() for e in self.agent_envelopes],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "verification": self.verification.to_dict(),
            "provenance_chain": self.provenance_chain,
            "human_review_packet": self.human_review_packet,
        }
