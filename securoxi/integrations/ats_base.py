"""
SECUROXI AI Phase 3 Stage 5 — Base ATS Integration Adapter Interface
Defines provider-agnostic ATS interfaces for candidate resume ingestion, job description ingestion,
webhook verification, idempotency deduplication, and screening result synchronization.
"""

import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class ATSWebhookEvent:
    """Normalized ATS webhook payload event."""
    event_id: str
    event_type: str  # "CANDIDATE_CREATED", "RESUME_ATTACHED", "JOB_CREATED"
    provider_name: str
    candidate_id: str
    job_id: Optional[str] = None
    file_path: Optional[str] = None
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "provider_name": self.provider_name,
            "candidate_id": self.candidate_id,
            "job_id": self.job_id,
            "file_path": self.file_path,
            "raw_payload": self.raw_payload,
            "timestamp": self.timestamp
        }


@dataclass
class ATSAuthenticationConfig:
    """Secure credentials configuration for ATS provider integration."""
    provider_name: str
    api_key: str
    webhook_secret: str
    base_url: str = "https://api.ats-provider.com/v1"


@dataclass
class ATSActionResult:
    """Result of an ATS operation or webhook processing."""
    success: bool
    operation: str
    message: str
    event_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


class BaseATSAdapter(ABC):
    """Abstract Base Class for Enterprise Applicant Tracking System (ATS) Adapters."""

    def __init__(self, config: ATSAuthenticationConfig):
        self.config = config
        self._processed_event_ids: set = set()  # Idempotency deduplication store

    @abstractmethod
    def verify_webhook_signature(self, raw_body: bytes, signature_header: str) -> bool:
        """Verifies HMAC signature of incoming ATS webhook."""
        pass

    @abstractmethod
    def parse_webhook_event(self, payload: Dict[str, Any]) -> ATSWebhookEvent:
        """Parses provider-specific webhook into a normalized ATSWebhookEvent."""
        pass

    @abstractmethod
    def sync_screening_result(self, candidate_id: str, screening_report: Dict[str, Any]) -> ATSActionResult:
        """Pushes SECUROXI security verdict & fit score back to the target ATS."""
        pass

    def is_duplicate_event(self, event_id: str) -> bool:
        """Idempotency check: returns True if event_id has already been processed."""
        if event_id in self._processed_event_ids:
            return True
        self._processed_event_ids.add(event_id)
        return False
