"""
SECUROXI AI Intelligence 2.0 — Cross-System Autonomous Investigation Models (Phase 8 Stage 49)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
import time
import uuid
from securoxi.enterprise.investigation.types import (
    TriggerType,
    TriggerSignificance,
    InvestigationStatus,
    HypothesisStatus,
    InvestigationFindingClass,
    ResponseActionType,
)


@dataclass
class TimelineEvent:
    """Chronological event record within an investigation case."""
    event_id: str = field(default_factory=lambda: f"TL-{uuid.uuid4().hex[:8].upper()}")
    source_system: str = "SECURITY"  # SECURITY, ATS, HIRING, KNOWLEDGE, AUDIT
    description: str = ""
    timestamp: float = field(default_factory=time.time)
    provenance_reference: str = ""


@dataclass
class InvestigationHypothesis:
    """Hypothesis tested during cross-system investigation."""
    hypothesis_id: str = field(default_factory=lambda: f"HYP-{uuid.uuid4().hex[:8].upper()}")
    case_id: str = "CASE-DEFAULT"
    description: str = "Proposed explanation"
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    confidence: float = 0.70
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class InvestigationRecommendation:
    """Grounded, governed response recommendation."""
    recommendation_id: str = field(default_factory=lambda: f"REC-{uuid.uuid4().hex[:8].upper()}")
    case_id: str = "CASE-DEFAULT"
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-SECURITY"
    action_type: ResponseActionType = ResponseActionType.QUARANTINE_RESOURCE
    target_resource_id: str = "RES-001"
    reason: str = "Confirmed prompt injection attempt on candidate resume"
    finding_class: InvestigationFindingClass = InvestigationFindingClass.CONFIRMED_SECURITY_ISSUE
    confidence: float = 0.95
    requires_approval: bool = True
    is_executed: bool = False
    created_at: float = field(default_factory=time.time)


@dataclass
class InvestigationCase:
    """Complete cross-system investigation case."""
    case_id: str = field(default_factory=lambda: f"CASE-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-SECURITY"
    trigger_type: TriggerType = TriggerType.REPEATED_SECURITY_FINDINGS
    significance: TriggerSignificance = TriggerSignificance.HIGH
    status: InvestigationStatus = InvestigationStatus.INITIATED
    target_resource_id: str = "RES-001"
    timeline: List[TimelineEvent] = field(default_factory=list)
    hypotheses: List[InvestigationHypothesis] = field(default_factory=list)
    recommendations: List[InvestigationRecommendation] = field(default_factory=list)
    finding_class: InvestigationFindingClass = InvestigationFindingClass.UNRESOLVED
    max_budget_steps: int = 10
    steps_executed: int = 0
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
