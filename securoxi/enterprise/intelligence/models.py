"""
SECUROXI AI Intelligence 2.0 — Continuous Enterprise Intelligence Models (Phase 8)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
import time
import uuid
from securoxi.enterprise.intelligence.types import (
    EventCategory,
    EventTrustLevel,
    EventSeverity,
    SignalType,
    SignalStatus,
    HypothesisStatus,
)


@dataclass
class EnterpriseEvent:
    """Canonical, strongly-typed immutable enterprise event."""
    event_id: str = field(default_factory=lambda: f"EVT-{uuid.uuid4().hex[:12].upper()}")
    event_type: str = "GENERIC_EVENT"
    category: EventCategory = EventCategory.SYSTEM
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-DEFAULT"
    actor_id: str = "SYSTEM"
    source: str = "securoxi.core"
    source_event_id: Optional[str] = None
    resource_type: str = "RESOURCE"
    resource_id: str = "RES-001"
    severity: EventSeverity = EventSeverity.NORMAL
    trust_level: EventTrustLevel = EventTrustLevel.AUTHORITATIVE_SYSTEM
    payload: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    received_at: float = field(default_factory=time.time)
    is_simulation: bool = False


@dataclass
class IntelligenceSignal:
    """Aggregated, correlated observation signal across events."""
    signal_id: str = field(default_factory=lambda: f"SIG-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-DEFAULT"
    signal_type: SignalType = SignalType.ANOMALOUS_ACTIVITY
    confidence: float = 0.85
    severity: EventSeverity = EventSeverity.HIGH
    status: SignalStatus = SignalStatus.DETECTED
    supporting_events: List[str] = field(default_factory=list)  # list of event_ids
    explanation: str = "Correlated pattern observed across system events"
    detected_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    occurrence_count: int = 1


@dataclass
class Hypothesis:
    """AI / Analytical advisory explanation for a signal."""
    hypothesis_id: str = field(default_factory=lambda: f"HYP-{uuid.uuid4().hex[:8].upper()}")
    signal_id: str = "SIG-DEFAULT"
    organization_id: str = "ORG-DEFAULT"
    explanation: str = "Proposed correlation hypothesis"
    confidence: float = 0.75
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    supporting_evidence: List[str] = field(default_factory=list)
    generated_by: str = "securoxi.correlation.ai"
    created_at: float = field(default_factory=time.time)
