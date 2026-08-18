"""
SECUROXI AI Intelligence 2.0 — Incident Agent Data Models
Defines strongly typed models for Incident Timeline Events, Correlations,
Proposals, and the top-level IncidentAgentResult contract.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import uuid
import time
from securoxi.orchestrator.agents.incident.types import (
    IncidentTriageSeverity,
    IncidentRecommendationType,
)


@dataclass
class IncidentTimelineEvent:
    """Individual chronological event in an incident audit trail."""
    timestamp: float = field(default_factory=time.time)
    event_name: str = "INCIDENT_EVENT"
    source: str = "SYSTEM"
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_name": self.event_name,
            "source": self.source,
            "details": self.details,
        }


@dataclass
class IncidentCorrelationItem:
    """Correlated security entity connected to the incident."""
    entity_id: str
    entity_type: str = "DOCUMENT"
    relationship: str = "AFFECTED_ASSET"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "relationship": self.relationship,
        }


@dataclass
class IncidentProposal:
    """Controlled response proposal submitted for human approval or automated policy evaluation."""
    proposal_id: str = field(default_factory=lambda: f"PROP-{uuid.uuid4().hex[:8].upper()}")
    action_type: str = "QUARANTINE"
    target_resources: List[str] = field(default_factory=list)
    reason: str = ""
    requires_human_approval: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "action_type": self.action_type,
            "target_resources": self.target_resources,
            "reason": self.reason,
            "requires_human_approval": self.requires_human_approval,
        }


@dataclass
class IncidentAgentResult:
    """Comprehensive structured incident report produced by the Incident Agent."""
    incident_id: str = ""
    lifecycle_state: str = "TRIAGED"
    severity: str = "HIGH"
    timeline: List[IncidentTimelineEvent] = field(default_factory=list)
    correlations: List[IncidentCorrelationItem] = field(default_factory=list)
    proposals: List[IncidentProposal] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "lifecycle_state": self.lifecycle_state,
            "severity": self.severity,
            "timeline": [t.to_dict() for t in self.timeline],
            "correlations": [c.to_dict() for c in self.correlations],
            "proposals": [p.to_dict() for p in self.proposals],
            "summary": self.summary,
        }
