"""
SECUROXI AI Intelligence 2.0 — Continuous Enterprise Intelligence Package (Phase 8)
"""

from securoxi.enterprise.intelligence.types import (
    EventCategory,
    EventTrustLevel,
    EventSeverity,
    SignalType,
    SignalStatus,
    HypothesisStatus,
)
from securoxi.enterprise.intelligence.models import (
    EnterpriseEvent,
    IntelligenceSignal,
    Hypothesis,
)
from securoxi.enterprise.intelligence.normalizer import EventNormalizer
from securoxi.enterprise.intelligence.correlation import ContinuousCorrelationEngine
from securoxi.enterprise.intelligence.manager import ContinuousEnterpriseIntelligenceManager

__all__ = [
    "EventCategory",
    "EventTrustLevel",
    "EventSeverity",
    "SignalType",
    "SignalStatus",
    "HypothesisStatus",
    "EnterpriseEvent",
    "IntelligenceSignal",
    "Hypothesis",
    "EventNormalizer",
    "ContinuousCorrelationEngine",
    "ContinuousEnterpriseIntelligenceManager",
]
