"""
SECUROXI AI Phase 3 Stage 1 — Security Brain Data Schemas & Event Models
Defines normalized security signals, events, correlation objects, attack chain graphs, and policy decisions.
"""

import time
import uuid
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


class SignalSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EventSource(str, Enum):
    DOCUMENT_PARSER = "DOCUMENT_PARSER"
    VISUAL_ANALYZER = "VISUAL_ANALYZER"
    PROMPT_INJECTION_DETECTOR = "PROMPT_INJECTION_DETECTOR"
    AI_REASONING_LAYER = "AI_REASONING_LAYER"
    RESUME_SCREENING_ENGINE = "RESUME_SCREENING_ENGINE"
    ATS_INTEGRATION_WEBHOOK = "ATS_INTEGRATION_WEBHOOK"
    AGENT_TOOL_CALL = "AGENT_TOOL_CALL"
    CONTINUOUS_MONITOR = "CONTINUOUS_MONITOR"


class PolicyAction(str, Enum):
    ALLOW = "ALLOW"
    WARN_AUDIT = "WARN_AUDIT"
    SUSPEND_SCREENING = "SUSPEND_SCREENING"
    QUARANTINE_BLOCK = "QUARANTINE_BLOCK"
    REVOKE_API_ACCESS = "REVOKE_API_ACCESS"


@dataclass
class SecuritySignal:
    """Raw or processed security signal collected from document, ATS, or agent event."""
    signal_id: str = field(default_factory=lambda: f"SIG-{uuid.uuid4().hex[:8]}")
    source: EventSource = EventSource.DOCUMENT_PARSER
    signal_type: str = "GENERIC_SIGNAL"
    severity: SignalSeverity = SignalSeverity.INFO
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    provenance_location: str = "UNKNOWN"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "source": self.source.value if hasattr(self.source, "value") else str(self.source),
            "signal_type": self.signal_type,
            "severity": self.severity.value if hasattr(self.severity, "value") else str(self.severity),
            "raw_payload": self.raw_payload,
            "provenance_location": self.provenance_location,
            "timestamp": self.timestamp
        }


@dataclass
class ThreatEntity:
    """Entity node inside the Security Brain attack graph."""
    entity_id: str
    entity_type: str  # "DOCUMENT", "CANDIDATE", "ATS_USER", "PROMPT_PAYLOAD", "TOOL_CALL"
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "attributes": self.attributes
        }


@dataclass
class CorrelationObject:
    """Synthesized security incident correlating signals across documents, ATS events, and tool calls."""
    incident_id: str = field(default_factory=lambda: f"INC-{uuid.uuid4().hex[:8]}")
    primary_threat_type: str = "UNASSIGNED"
    correlated_signal_ids: List[str] = field(default_factory=list)
    affected_entities: List[ThreatEntity] = field(default_factory=list)
    composite_risk_score: float = 0.0
    attack_chain_summary: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "primary_threat_type": self.primary_threat_type,
            "correlated_signal_ids": self.correlated_signal_ids,
            "affected_entities": [e.to_dict() for e in self.affected_entities],
            "composite_risk_score": self.composite_risk_score,
            "attack_chain_summary": self.attack_chain_summary,
            "timestamp": self.timestamp
        }


@dataclass
class AttackChainGraph:
    """Graph representation of multi-stage attack vectors across ATS and document pipelines."""
    graph_id: str = field(default_factory=lambda: f"ACG-{uuid.uuid4().hex[:8]}")
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)

    def add_node(self, node_id: str, label: str, node_type: str):
        self.nodes.append({"id": node_id, "label": label, "type": node_type})

    def add_edge(self, source_id: str, target_id: str, relationship: str):
        self.edges.append({"source": source_id, "target": target_id, "relationship": relationship})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "nodes": self.nodes,
            "edges": self.edges
        }


@dataclass
class PolicyDecision:
    """Enforced policy outcome produced by Security Brain."""
    decision_id: str = field(default_factory=lambda: f"DEC-{uuid.uuid4().hex[:8]}")
    action: PolicyAction = PolicyAction.ALLOW
    risk_score: float = 0.0
    reasoning: str = "Evaluation passed security policy bounds."
    enforced_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "action": self.action.value if hasattr(self.action, "value") else str(self.action),
            "risk_score": self.risk_score,
            "reasoning": self.reasoning,
            "enforced_at": self.enforced_at
        }
