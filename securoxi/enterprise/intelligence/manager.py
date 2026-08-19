"""
SECUROXI AI Intelligence 2.0 — Continuous Enterprise Intelligence Manager (Phase 8 Stage 45)
Coordinates multi-source event ingestion, normalization, bounded correlation,
signal lifecycle management, and simulation replay.
"""

from typing import Dict, Any, List, Optional, Set
import time
from securoxi.enterprise.intelligence.types import (
    EventTrustLevel,
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
from securoxi.logger import get_logger

logger = get_logger("enterprise.intelligence.manager")


class ContinuousEnterpriseIntelligenceManager:
    """
    Enterprise Continuous Intelligence Substrate Manager.
    Aggregates authorized enterprise events and produces structured signals for downstream autonomy.
    """

    def __init__(self, window_seconds: float = 300.0):
        self.normalizer = EventNormalizer()
        self.engine = ContinuousCorrelationEngine(window_seconds=window_seconds)
        self._raw_events: List[EnterpriseEvent] = []
        self._dedup_keys: Set[str] = set()

    def ingest_event(
        self,
        raw_event: Dict[str, Any],
        organization_id: str,
        workspace_id: str = "WS-DEFAULT",
        source: str = "securoxi.gateway",
        trust_level: EventTrustLevel = EventTrustLevel.EXTERNAL_UNTRUSTED,
    ) -> Optional[IntelligenceSignal]:
        """Ingests, validates, normalizes, deduplicates, and correlates an incoming enterprise event."""
        event = self.normalizer.normalize(
            raw_event=raw_event,
            organization_id=organization_id,
            workspace_id=workspace_id,
            source=source,
            trust_level=trust_level,
        )
        if not event:
            return None

        # Deduplication check
        dedup_key = f"{event.organization_id}:{event.source_event_id or event.event_id}:{event.event_type}"
        if dedup_key in self._dedup_keys:
            logger.info(f"Event '{dedup_key}' deduplicated - ignoring duplicate")
            return None

        self._dedup_keys.add(dedup_key)
        self._raw_events.append(event)

        # Correlate event into signals
        signal = self.engine.correlate_event(event)
        return signal

    def get_signals(self, organization_id: str, workspace_id: Optional[str] = None) -> List[IntelligenceSignal]:
        """Returns signals strictly scoped by tenant."""
        return self.engine.get_signals_for_org(organization_id, workspace_id)

    def get_hypotheses(self, signal_id: str) -> List[Hypothesis]:
        """Returns AI advisory hypotheses for a signal."""
        return self.engine.get_hypotheses_for_signal(signal_id)

    def dismiss_signal(self, signal_id: str, analyst_id: str, reason: str) -> bool:
        """Dismisses a false-positive or non-actionable signal with feedback reason."""
        if signal_id in self.engine._signals:
            sig = self.engine._signals[signal_id]
            sig.status = SignalStatus.DISMISSED
            logger.info(f"Signal '{signal_id}' dismissed by Analyst '{analyst_id}': {reason}")
            return True
        return False

    def replay_events(self, raw_events: List[Dict[str, Any]], organization_id: str) -> List[IntelligenceSignal]:
        """Replays historical events safely in simulation mode (zero external mutations)."""
        replayed_signals = []
        for raw in raw_events:
            evt = self.normalizer.normalize(
                raw_event=raw,
                organization_id=organization_id,
                source="securoxi.replay",
                trust_level=EventTrustLevel.VERIFIED_APPLICATION,
            )
            if evt:
                evt.is_simulation = True
                sig = self.engine.correlate_event(evt)
                if sig:
                    replayed_signals.append(sig)
        return replayed_signals
