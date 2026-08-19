"""
SECUROXI AI Intelligence 2.0 — Enterprise Developer Platform & Webhooks Test Suite (Stage 41)
Validates API Key provisioning, granular scope authorization, task creation idempotency,
outbound webhook HMAC signing, SSRF protection, and key revocation.
"""

import pytest
from securoxi.enterprise.developer import (
    EnterpriseAPIManager,
    APIScope,
    WebhookEventType,
    WebhookDeliveryStatus,
)


# =========================================================================
# 1. API KEY AUTHENTICATION & SCOPE ENFORCEMENT
# =========================================================================

def test_api_key_authentication_and_scope_enforcement():
    """Verifies API key creation, hashed storage, and granular scope validation."""
    api_mgr = EnterpriseAPIManager()

    # 1. Create Key with Task Read & Create scopes
    key, raw_secret = api_mgr.create_api_key(
        organization_id="ORG-ACME",
        name="CI/CD Task Runner",
        scopes={APIScope.TASK_READ, APIScope.TASK_CREATE},
    )

    # 2. Authenticate with valid key and valid scope
    auth_key = api_mgr.authenticate_api_key(raw_secret, required_scope=APIScope.TASK_CREATE)
    assert auth_key is not None
    assert auth_key.organization_id == "ORG-ACME"

    # 3. Authenticate with ungranted scope -> DENIED
    denied_key = api_mgr.authenticate_api_key(raw_secret, required_scope=APIScope.ATS_WRITE)
    assert denied_key is None

    # 4. Revoke Key -> Subsequent auth MUST FAIL
    api_mgr.revoke_api_key(key.key_id)
    revoked_auth = api_mgr.authenticate_api_key(raw_secret, required_scope=APIScope.TASK_CREATE)
    assert revoked_auth is None


# =========================================================================
# 2. IDEMPOTENT TASK CREATION
# =========================================================================

def test_api_task_creation_idempotency():
    """Verifies that submitting repeated requests with the same Idempotency-Key returns cached results."""
    api_mgr = EnterpriseAPIManager()

    key, raw_secret = api_mgr.create_api_key("ORG-ACME", scopes={APIScope.TASK_CREATE})

    # 1. First Task Creation Request
    res_1 = api_mgr.create_task_via_api(
        api_key=key,
        objective="Screen 50 candidate resumes",
        idempotency_key="req_idemp_101",
    )
    task_id_1 = res_1["task_id"]

    # 2. Duplicate Request with identical Idempotency-Key
    res_2 = api_mgr.create_task_via_api(
        api_key=key,
        objective="Screen 50 candidate resumes",
        idempotency_key="req_idemp_101",
    )
    task_id_2 = res_2["task_id"]

    # MUST Return exact same task (Idempotency Cache Hit)
    assert task_id_1 == task_id_2


# =========================================================================
# 3. WEBHOOK SSRF PROTECTION & HMAC SIGNING
# =========================================================================

def test_webhook_ssrf_protection_and_hmac_signing():
    """Verifies that webhooks reject internal/loopback IPs and sign valid outbound payloads."""
    api_mgr = EnterpriseAPIManager()

    # 1. SSRF Attack Attempt (Localhost / AWS Metadata IP) -> REGISTRATION BLOCKED
    ssrf_sub = api_mgr.register_webhook_subscription(
        organization_id="ORG-ACME",
        endpoint_url="http://169.254.169.254/latest/meta-data",
    )
    assert ssrf_sub is None

    loopback_sub = api_mgr.register_webhook_subscription(
        organization_id="ORG-ACME",
        endpoint_url="http://localhost:8080/hook",
    )
    assert loopback_sub is None

    # 2. Valid External Webhook Subscription
    valid_sub = api_mgr.register_webhook_subscription(
        organization_id="ORG-ACME",
        endpoint_url="https://api.customer.com/webhooks/securoxi",
        event_types={WebhookEventType.TASK_COMPLETED},
    )
    assert valid_sub is not None

    # 3. Emit Task Completed Event
    dispatches = api_mgr.emit_event(
        organization_id="ORG-ACME",
        event_type=WebhookEventType.TASK_COMPLETED,
        data={"task_id": "TASK-123", "status": "COMPLETED"},
    )

    assert len(dispatches) == 1
    assert dispatches[0]["status"] == WebhookDeliveryStatus.DELIVERED.value
    delivery_rec = dispatches[0]["delivery_record"]
    assert "t=" in delivery_rec["signature"]
    assert "v1=" in delivery_rec["signature"]
