"""
SECUROXI AI Intelligence 2.0 — Production Readiness & Deployment Hardening Test Suite (Stage 25)
Validates environment configuration rules, production health/liveness probes, secret exclusion,
CORS allowlist enforcement, database connection stability, and multi-tenant isolation.
"""

import pytest
from fastapi.testclient import TestClient
from securoxi.api.app import app
from securoxi.environment import (
    EnvironmentMode,
    ProductionDeploymentConfig,
    validate_environment,
    load_deployment_config,
)


@pytest.fixture
def client():
    return TestClient(app)


# =========================================================================
# 1. ENVIRONMENT CONFIGURATION & VALIDATION
# =========================================================================

def test_development_environment_configuration():
    """Verifies that development configuration loads with safe defaults."""
    cfg = ProductionDeploymentConfig(
        environment=EnvironmentMode.DEVELOPMENT,
        api_key="securoxi-enterprise-key",
        cors_allowed_origins=["http://localhost:5173", "http://localhost:8000"],
    )
    issues = validate_environment(cfg)
    assert len(issues) == 0


def test_production_environment_flags_insecure_defaults():
    """Verifies that production mode detects and rejects insecure default keys and wildcard CORS."""
    bad_prod_cfg = ProductionDeploymentConfig(
        environment=EnvironmentMode.PRODUCTION,
        api_key="securoxi-enterprise-key",  # Default key
        cors_allowed_origins=["*"],          # Wildcard CORS
        ai_provider="gemini",
        gemini_api_key=None,                 # Missing key
    )
    issues = validate_environment(bad_prod_cfg)
    assert len(issues) >= 3
    issue_text = " ".join(issues)
    assert "PRODUCTION_INSECURE_DEFAULT_API_KEY" in issue_text
    assert "PRODUCTION_INSECURE_CORS" in issue_text
    assert "PRODUCTION_MISSING_AI_KEY" in issue_text


def test_production_environment_accepts_hardened_config():
    """Verifies that valid production configuration passes validation without warnings."""
    good_prod_cfg = ProductionDeploymentConfig(
        environment=EnvironmentMode.PRODUCTION,
        api_key="sec-prod-super-secure-key-9921",
        cors_allowed_origins=["https://app.securoxi.ai", "https://securoxi.ai"],
        ai_provider="mock",
    )
    issues = validate_environment(good_prod_cfg)
    assert len(issues) == 0


# =========================================================================
# 2. HEALTH & READINESS PROBES
# =========================================================================

def test_health_liveness_probe(client):
    """Verifies /api/v1/health/liveness returns valid process status."""
    response = client.get("/api/v1/health/liveness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_health_readiness_probe(client):
    """Verifies /api/v1/health/readiness verifies database connectivity."""
    response = client.get("/api/v1/health/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "healthy"
    assert data["broker"] == "healthy"


# =========================================================================
# 3. SECURITY HEADERS & SECRET SANITIZATION
# =========================================================================

def test_security_headers_present_in_api_responses(client):
    """Verifies that production security headers are set on all HTTP responses."""
    response = client.get("/api/v1/health/liveness")
    headers = response.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert "Strict-Transport-Security" in headers
    assert "Content-Security-Policy" in headers


def test_error_response_sanitizes_internal_secrets(client):
    """Verifies that invalid requests return clean error messages without stack traces or secret dumps."""
    response = client.post(
        "/api/v1/agentic/task/submit",
        headers={"X-API-Key": "invalid-key-xyz", "X-Tenant-ID": "TENANT-01"},
        json={"objective": "Test"},
    )
    assert response.status_code == 401
    detail = response.json().get("detail", "")
    assert "Traceback" not in detail
    assert "password" not in detail.lower()
    assert "secret" not in detail.lower()
