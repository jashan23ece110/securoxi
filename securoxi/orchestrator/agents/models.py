"""
SECUROXI AI Intelligence 2.0 — Agent Runtime Data Models
Defines strongly typed contracts for Agent Definitions, Inputs, Observations,
Decisions, Outputs, Handoffs, and Observability Traces.
"""

import time
import uuid
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field

from securoxi.orchestrator.types import TrustLevel
from securoxi.orchestrator.planning.types import TaskIntent
from securoxi.orchestrator.agents.types import (
    AgentDomain,
    AgentCapability,
    AgentRiskLevel,
    AgentLifecycleState,
    AgentActionType,
    MemoryAccessPermission,
)


@dataclass
class AgentDefinition:
    """System-owned declarative definition and permissions for an agent."""
    agent_id: str = ""
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    domain: AgentDomain = AgentDomain.GENERAL
    capabilities: List[AgentCapability] = field(default_factory=list)
    trust_level: TrustLevel = TrustLevel.CONTROLLED
    risk_level: AgentRiskLevel = AgentRiskLevel.LOW
    allowed_tools: Set[str] = field(default_factory=set)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    memory_scopes: Set[MemoryAccessPermission] = field(default_factory=lambda: {
        MemoryAccessPermission.READ_WORKING,
        MemoryAccessPermission.WRITE_WORKING,
        MemoryAccessPermission.READ_TASK,
    })
    supported_intents: List[TaskIntent] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    max_iterations: int = 20
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "domain": self.domain.value,
            "capabilities": [c.value for c in self.capabilities],
            "trust_level": self.trust_level.value,
            "risk_level": self.risk_level.value,
            "allowed_tools": sorted(list(self.allowed_tools)),
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "memory_scopes": [m.value for m in self.memory_scopes],
            "supported_intents": [i.value for i in self.supported_intents],
            "dependencies": self.dependencies,
            "max_iterations": self.max_iterations,
            "enabled": self.enabled,
        }


@dataclass
class AgentInput:
    """Structured input payload delivered to an agent for node execution."""
    task_id: str = ""
    run_id: str = ""
    node_id: str = ""
    tenant_id: str = "TENANT-DEFAULT"
    actor_id: str = "SYSTEM"
    intent: TaskIntent = TaskIntent.DOCUMENT_SCAN
    parameters: Dict[str, Any] = field(default_factory=dict)
    evidence_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "run_id": self.run_id,
            "node_id": self.node_id,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "intent": self.intent.value,
            "parameters": self.parameters,
            "evidence_context": self.evidence_context,
        }


@dataclass
class AgentObservation:
    """A unit of observed environment data, tool output, or peer agent result."""
    observation_id: str = field(default_factory=lambda: f"OBS-{uuid.uuid4().hex[:8].upper()}")
    source: str = "TOOL_RESULT"  # "TOOL_RESULT", "DOCUMENT_EVIDENCE", "PEER_AGENT_OUTPUT", "POLICY_STATE"
    payload: Any = None
    provenance: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "source": self.source,
            "payload": self.payload,
            "provenance": self.provenance,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentDecision:
    """A structured action proposal submitted by an agent to the orchestrator."""
    decision_type: AgentActionType = AgentActionType.CONTINUE
    target_tool_id: Optional[str] = None
    tool_arguments: Dict[str, Any] = field(default_factory=dict)
    target_agent_id: Optional[str] = None
    handoff_payload: Dict[str, Any] = field(default_factory=dict)
    clarification_question: Optional[str] = None
    reasoning_summary: str = ""
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_type": self.decision_type.value,
            "target_tool_id": self.target_tool_id,
            "tool_arguments": self.tool_arguments,
            "target_agent_id": self.target_agent_id,
            "handoff_payload": self.handoff_payload,
            "clarification_question": self.clarification_question,
            "reasoning_summary": self.reasoning_summary,
            "confidence": self.confidence,
        }


@dataclass
class AgentOutput:
    """Validated output produced by an agent upon task completion."""
    agent_id: str = ""
    version: str = "1.0.0"
    status: AgentLifecycleState = AgentLifecycleState.COMPLETED
    result_data: Dict[str, Any] = field(default_factory=dict)
    evidence_references: List[str] = field(default_factory=list)
    provenance: List[str] = field(default_factory=list)
    recommended_next_steps: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "version": self.version,
            "status": self.status.value,
            "result_data": self.result_data,
            "evidence_references": self.evidence_references,
            "provenance": self.provenance,
            "recommended_next_steps": self.recommended_next_steps,
            "warnings": self.warnings,
            "confidence": self.confidence,
        }


@dataclass
class AgentHandoffContract:
    """Structured work handoff payload between peer agents."""
    handoff_id: str = field(default_factory=lambda: f"HANDOFF-{uuid.uuid4().hex[:8].upper()}")
    source_agent_id: str = ""
    target_agent_id: str = ""
    tenant_id: str = "TENANT-DEFAULT"
    handoff_data: Dict[str, Any] = field(default_factory=dict)
    trust_level: TrustLevel = TrustLevel.CONTROLLED
    provenance_chain: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "handoff_id": self.handoff_id,
            "source_agent_id": self.source_agent_id,
            "target_agent_id": self.target_agent_id,
            "tenant_id": self.tenant_id,
            "handoff_data": self.handoff_data,
            "trust_level": self.trust_level.value,
            "provenance_chain": self.provenance_chain,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentTraceRecord:
    """Audit trace of an agent's execution steps, decisions, and tool dispatches."""
    trace_id: str = field(default_factory=lambda: f"ATRACE-{uuid.uuid4().hex[:8].upper()}")
    agent_id: str = ""
    version: str = "1.0.0"
    task_id: str = ""
    run_id: str = ""
    node_id: str = ""
    tenant_id: str = "TENANT-DEFAULT"
    steps: List[Dict[str, Any]] = field(default_factory=list)
    tools_invoked: List[str] = field(default_factory=list)
    tools_denied: List[str] = field(default_factory=list)
    handoffs: List[str] = field(default_factory=list)
    duration_ms: float = 0.0
    budget_usage: Dict[str, Any] = field(default_factory=dict)
    final_status: str = "COMPLETED"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "agent_id": self.agent_id,
            "version": self.version,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "node_id": self.node_id,
            "tenant_id": self.tenant_id,
            "steps": self.steps,
            "tools_invoked": self.tools_invoked,
            "tools_denied": self.tools_denied,
            "handoffs": self.handoffs,
            "duration_ms": self.duration_ms,
            "budget_usage": self.budget_usage,
            "final_status": self.final_status,
            "timestamp": self.timestamp,
        }
