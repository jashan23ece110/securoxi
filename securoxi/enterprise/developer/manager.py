"""
SECUROXI AI Intelligence 2.0 — Enterprise Developer Platform & API Manager
Coordinates API Key authentication, scope authorization, task creation idempotency,
and outbound webhook subscriptions.
"""

from typing import Dict, Any, List, Set, Optional
import hashlib
import uuid
import time
from securoxi.enterprise.developer.types import (
    APIScope,
    WebhookEventType,
)
from securoxi.enterprise.developer.models import (
    APIKey,
    WebhookSubscription,
    WebhookEventPayload,
    IdempotencyRecord,
)
from securoxi.enterprise.developer.webhooks import EnterpriseWebhookDispatcher
from securoxi.logger import get_logger

logger = get_logger("enterprise.developer")


class EnterpriseAPIManager:
    """
    Enterprise Developer API Engine.
    Manages API keys, scope enforcement, task creation with idempotency, and webhook subscriptions.
    """

    def __init__(self):
        self._keys: Dict[str, APIKey] = {}  # hashed_secret -> APIKey
        self._keys_by_id: Dict[str, APIKey] = {}
        self._subscriptions: Dict[str, WebhookSubscription] = {}
        self._idempotency_store: Dict[str, IdempotencyRecord] = {}  # scoped_key -> record
        self.dispatcher = EnterpriseWebhookDispatcher()

    def create_api_key(
        self,
        organization_id: str,
        name: str = "Enterprise API Key",
        scopes: Optional[Set[APIScope]] = None,
        workspace_id: Optional[str] = None,
    ) -> tuple[APIKey, str]:
        """Generates a secure high-entropy API key and stores its hash."""
        raw_secret = f"securoxi_live_{uuid.uuid4().hex}{uuid.uuid4().hex[:8]}"
        hashed_secret = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()

        active_scopes = scopes or {APIScope.TASK_READ, APIScope.TASK_CREATE}

        key = APIKey(
            organization_id=organization_id,
            workspace_id=workspace_id,
            name=name,
            scopes=active_scopes,
            hashed_secret=hashed_secret,
        )
        self._keys[hashed_secret] = key
        self._keys_by_id[key.key_id] = key

        logger.info(f"Created API Key '{key.key_id}' for Org '{organization_id}' with scopes {[s.value for s in active_scopes]}")
        return key, raw_secret

    def revoke_api_key(self, key_id: str) -> bool:
        """Revokes an active API key immediately."""
        if key_id not in self._keys_by_id:
            return False

        key = self._keys_by_id[key_id]
        key.is_active = False
        logger.info(f"Revoked API Key '{key_id}'")
        return True

    def authenticate_api_key(self, raw_secret: str, required_scope: Optional[APIScope] = None) -> Optional[APIKey]:
        """Validates API key credentials and verifies required scope."""
        hashed = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()
        if hashed not in self._keys:
            return None

        key = self._keys[hashed]
        if not key.is_active:
            return None

        if required_scope and not key.has_scope(required_scope):
            logger.warning(f"API Scope Check Failed: Key '{key.key_id}' lacks required scope '{required_scope.value}'")
            return None

        key.last_used_at = time.time()
        return key

    def create_task_via_api(
        self,
        api_key: APIKey,
        objective: str,
        context_data: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Creates an autonomous task via API with idempotency deduplication.
        """
        if not api_key.has_scope(APIScope.TASK_CREATE):
            return {"error": "Missing task:create scope"}

        # Check Idempotency Key
        if idempotency_key:
            scoped_idempotency_key = f"{api_key.organization_id}:{idempotency_key}"
            if scoped_idempotency_key in self._idempotency_store:
                logger.info(f"Idempotency Cache Hit: Returning cached response for key '{idempotency_key}'")
                return self._idempotency_store[scoped_idempotency_key].response_payload

        # Create Task
        task_id = f"TASK-API-{uuid.uuid4().hex[:8].upper()}"
        response = {
            "task_id": task_id,
            "organization_id": api_key.organization_id,
            "workspace_id": api_key.workspace_id,
            "objective": objective,
            "status": "RUNNING",
            "created_at": time.time(),
        }

        if idempotency_key:
            scoped_idempotency_key = f"{api_key.organization_id}:{idempotency_key}"
            self._idempotency_store[scoped_idempotency_key] = IdempotencyRecord(
                idempotency_key=idempotency_key,
                organization_id=api_key.organization_id,
                principal_id=api_key.key_id,
                response_payload=response,
            )

        logger.info(f"API Created Task '{task_id}' for Org '{api_key.organization_id}'")
        return response

    def register_webhook_subscription(
        self,
        organization_id: str,
        endpoint_url: str,
        event_types: Optional[Set[WebhookEventType]] = None,
        workspace_id: Optional[str] = None,
    ) -> Optional[WebhookSubscription]:
        """Registers a new outbound webhook subscription."""
        if not self.dispatcher.is_safe_endpoint(endpoint_url):
            logger.error(f"Cannot register Webhook: Endpoint '{endpoint_url}' failed SSRF safety checks")
            return None

        events = event_types or {WebhookEventType.TASK_COMPLETED}
        sub = WebhookSubscription(
            organization_id=organization_id,
            workspace_id=workspace_id,
            endpoint_url=endpoint_url,
            event_types=events,
        )
        self._subscriptions[sub.subscription_id] = sub
        logger.info(f"Registered Webhook Subscription '{sub.subscription_id}' for Org '{organization_id}' -> '{endpoint_url}'")
        return sub

    def emit_event(
        self,
        organization_id: str,
        event_type: WebhookEventType,
        data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Dispatches an event to all matching organization webhook subscriptions."""
        dispatches = []
        payload = WebhookEventPayload(
            event_type=event_type,
            organization_id=organization_id,
            data=data,
        )

        for sub in self._subscriptions.values():
            if sub.organization_id == organization_id and sub.is_active and event_type in sub.event_types:
                res = self.dispatcher.dispatch_event(sub, payload)
                dispatches.append(res)

        return dispatches
