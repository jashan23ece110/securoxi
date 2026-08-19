"""
SECUROXI AI Intelligence 2.0 — Event Normalizer & Validator (Phase 8)
Transforms heterogeneous external payloads into canonical EnterpriseEvents.
Strictly treats external payload content as data rather than instructions.
"""

from typing import Dict, Any, Optional
import time
from securoxi.enterprise.intelligence.types import (
    EventCategory,
    EventTrustLevel,
    EventSeverity,
)
from securoxi.enterprise.intelligence.models import EnterpriseEvent
from securoxi.logger import get_logger

logger = get_logger("enterprise.intelligence.normalizer")


class EventNormalizer:
    """Canonical Normalizer and Schema Validator for Enterprise Events."""

    @staticmethod
    def normalize(
        raw_event: Dict[str, Any],
        organization_id: str,
        workspace_id: str = "WS-DEFAULT",
        source: str = "securoxi.gateway",
        trust_level: EventTrustLevel = EventTrustLevel.EXTERNAL_UNTRUSTED,
    ) -> Optional[EnterpriseEvent]:
        """Normalizes external dictionary or event payload into typed EnterpriseEvent."""
        if not organization_id:
            logger.warning("Event normalization rejected: Missing organization_id")
            return None

        event_type = raw_event.get("event_type", "GENERIC_EVENT")
        resource_id = raw_event.get("resource_id", "RES-UNKNOWN")
        resource_type = raw_event.get("resource_type", "RESOURCE")
        source_event_id = raw_event.get("source_event_id", raw_event.get("id"))
        
        # Categorize
        category = EventCategory.SYSTEM
        if "SECURITY" in event_type or "FINDING" in event_type or "INJECTION" in event_type:
            category = EventCategory.SECURITY
        elif "CANDIDATE" in event_type or "RESUME" in event_type or "HIRING" in event_type or "ATS" in event_type:
            category = EventCategory.HIRING
        elif "TASK" in event_type:
            category = EventCategory.TASK
        elif "GOVERNANCE" in event_type or "DOCUMENT" in event_type or "HOLD" in event_type:
            category = EventCategory.DATA_GOVERNANCE

        # Severity
        raw_sev = raw_event.get("severity", "NORMAL").upper()
        severity = EventSeverity.NORMAL
        if raw_sev in EventSeverity.__members__:
            severity = EventSeverity[raw_sev]

        # Extract payload safely (never execute or parse as instruction)
        payload = raw_event.get("payload", raw_event)

        event = EnterpriseEvent(
            event_type=event_type,
            category=category,
            organization_id=organization_id,
            workspace_id=workspace_id,
            actor_id=raw_event.get("actor_id", "ANONYMOUS"),
            source=source,
            source_event_id=source_event_id,
            resource_type=resource_type,
            resource_id=resource_id,
            severity=severity,
            trust_level=trust_level,
            payload=payload if isinstance(payload, dict) else {"data": payload},
            correlation_id=raw_event.get("correlation_id"),
            causation_id=raw_event.get("causation_id"),
            timestamp=float(raw_event.get("timestamp", time.time())),
            received_at=time.time(),
        )
        return event
