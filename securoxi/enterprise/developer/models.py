"""
SECUROXI AI Intelligence 2.0 — Enterprise Developer Platform & Webhook Models
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Set, Optional
import time
import uuid
from securoxi.enterprise.developer.types import (
    APIScope,
    WebhookEventType,
    WebhookDeliveryStatus,
)


@dataclass
class APIKey:
    """Enterprise API Key with granular scopes and organization/workspace binding."""
    key_id: str = field(default_factory=lambda: f"KEY-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: Optional[str] = None
    name: str = "Default API Key"
    scopes: Set[APIScope] = field(default_factory=lambda: {APIScope.TASK_READ, APIScope.TASK_CREATE})
    hashed_secret: str = ""
    is_active: bool = True
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    last_used_at: Optional[float] = None

    def has_scope(self, scope: APIScope) -> bool:
        return self.is_active and (scope in self.scopes)


@dataclass
class WebhookSubscription:
    """Outbound webhook subscription for enterprise event notifications."""
    subscription_id: str = field(default_factory=lambda: f"SUB-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: Optional[str] = None
    endpoint_url: str = "https://api.enterprise.com/webhooks"
    event_types: Set[WebhookEventType] = field(default_factory=lambda: {WebhookEventType.TASK_COMPLETED})
    secret: str = field(default_factory=lambda: f"whsec_{uuid.uuid4().hex}")
    is_active: bool = True
    created_at: float = field(default_factory=time.time)


@dataclass
class WebhookEventPayload:
    """Standardized outbound webhook event payload."""
    event_id: str = field(default_factory=lambda: f"EVT-{uuid.uuid4().hex[:8].upper()}")
    event_type: WebhookEventType = WebhookEventType.TASK_COMPLETED
    organization_id: str = "ORG-DEFAULT"
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    version: str = "v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "organization_id": self.organization_id,
            "data": self.data,
            "timestamp": self.timestamp,
            "version": self.version,
        }


@dataclass
class IdempotencyRecord:
    """Scoped idempotency token record preventing duplicate task creation."""
    idempotency_key: str
    organization_id: str
    principal_id: str
    response_payload: Dict[str, Any]
    created_at: float = field(default_factory=time.time)
