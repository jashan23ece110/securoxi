"""
SECUROXI AI Intelligence 2.0 — Continuous Correlation Engine (Phase 8)
Correlates enterprise events across temporal, entity, and pattern dimensions.
Enforces strict organization and workspace isolation.
"""

from typing import Dict, List, Any, Optional
import time
from securoxi.enterprise.intelligence.types import (
    EventCategory,
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
from securoxi.logger import get_logger

logger = get_logger("enterprise.intelligence.correlation")


class ContinuousCorrelationEngine:
    """
    Continuous Event Correlation Engine.
    Aggregates multi-source events into bounded-window intelligence signals.
    """

    def __init__(self, window_seconds: float = 300.0):
        self.window_seconds = window_seconds
        # org_id -> resource_id -> list of EnterpriseEvent
        self._entity_events: Dict[str, Dict[str, List[EnterpriseEvent]]] = {}
        # signal_id -> IntelligenceSignal
        self._signals: Dict[str, IntelligenceSignal] = {}
        # signal_id -> list of Hypothesis
        self._hypotheses: Dict[str, List[Hypothesis]] = {}

    def correlate_event(self, event: EnterpriseEvent) -> Optional[IntelligenceSignal]:
        """
        Ingests a normalized event and performs correlation against recent entity events
        strictly within the same organization.
        """
        org_id = event.organization_id
        res_id = event.resource_id

        if org_id not in self._entity_events:
            self._entity_events[org_id] = {}
        if res_id not in self._entity_events[org_id]:
            self._entity_events[org_id][res_id] = []

        # Prune old events outside the temporal window
        cutoff = event.timestamp - self.window_seconds
        recent_events = [e for e in self._entity_events[org_id][res_id] if e.timestamp >= cutoff]
        recent_events.append(event)
        self._entity_events[org_id][res_id] = recent_events

        # Pattern 1: Repeated Security Findings on the same resource
        sec_events = [e for e in recent_events if e.category == EventCategory.SECURITY]
        if len(sec_events) >= 2:
            sig = self._create_or_update_signal(
                org_id=org_id,
                workspace_id=event.workspace_id,
                signal_type=SignalType.REPEATED_SECURITY_FINDINGS,
                severity=EventSeverity.HIGH,
                events=sec_events,
                explanation=f"Multiple security findings ({len(sec_events)}) detected on resource '{res_id}' within {self.window_seconds}s",
            )
            # Create AI Advisory Hypothesis
            self._generate_advisory_hypothesis(
                sig=sig,
                explanation=f"Potential adversarial probe or repeated malicious payload submission targeting resource {res_id}",
            )
            return sig

        # Pattern 2: Suspicious Rapid Candidate Activity
        cand_events = [e for e in recent_events if e.category == EventCategory.HIRING]
        if len(cand_events) >= 3:
            sig = self._create_or_update_signal(
                org_id=org_id,
                workspace_id=event.workspace_id,
                signal_type=SignalType.SUSPICIOUS_CANDIDATE_ACTIVITY,
                severity=EventSeverity.NORMAL,
                events=cand_events,
                explanation=f"Rapid hiring/resume activity ({len(cand_events)} events) observed on candidate '{res_id}'",
            )
            return sig

        return None

    def _create_or_update_signal(
        self,
        org_id: str,
        workspace_id: str,
        signal_type: SignalType,
        severity: EventSeverity,
        events: List[EnterpriseEvent],
        explanation: str,
    ) -> IntelligenceSignal:
        """Deduplicates and creates/updates a signal."""
        # Find existing active signal for same org & signal_type & resource
        sig_key = f"{org_id}:{workspace_id}:{signal_type.value}:{events[0].resource_id}"
        
        for sig in self._signals.values():
            if (
                sig.organization_id == org_id
                and sig.workspace_id == workspace_id
                and sig.signal_type == signal_type
                and sig.status in {SignalStatus.DETECTED, SignalStatus.ENRICHED, SignalStatus.UNDER_REVIEW}
            ):
                sig.supporting_events = list(set(sig.supporting_events + [e.event_id for e in events]))
                sig.occurrence_count = len(sig.supporting_events)
                sig.updated_at = time.time()
                sig.explanation = explanation
                return sig

        # Create new signal
        new_sig = IntelligenceSignal(
            organization_id=org_id,
            workspace_id=workspace_id,
            signal_type=signal_type,
            confidence=0.88,
            severity=severity,
            status=SignalStatus.DETECTED,
            supporting_events=[e.event_id for e in events],
            explanation=explanation,
            occurrence_count=len(events),
        )
        self._signals[new_sig.signal_id] = new_sig
        logger.info(f"Created Intelligence Signal '{new_sig.signal_id}' ({signal_type.value}) for Org '{org_id}'")
        return new_sig

    def _generate_advisory_hypothesis(self, sig: IntelligenceSignal, explanation: str):
        """Generates an advisory analytical hypothesis (strictly non-authoritative)."""
        hyp = Hypothesis(
            signal_id=sig.signal_id,
            organization_id=sig.organization_id,
            explanation=explanation,
            confidence=0.80,
            status=HypothesisStatus.PROPOSED,
            supporting_evidence=sig.supporting_events,
        )
        if sig.signal_id not in self._hypotheses:
            self._hypotheses[sig.signal_id] = []
        self._hypotheses[sig.signal_id].append(hyp)

    def get_signals_for_org(self, organization_id: str, workspace_id: Optional[str] = None) -> List[IntelligenceSignal]:
        """Returns signals scoped strictly by organization and optional workspace."""
        results = [s for s in self._signals.values() if s.organization_id == organization_id]
        if workspace_id:
            results = [s for s in results if s.workspace_id == workspace_id]
        return results

    def get_hypotheses_for_signal(self, signal_id: str) -> List[Hypothesis]:
        return self._hypotheses.get(signal_id, [])
