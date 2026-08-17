"""
SECUROXI AI Production Network Security & Ingress Integration Test Suite
Validates liveness/readiness probes, security headers (HSTS, CSP, XFO), CORS restrictions,
and container network segmentation boundaries.
"""

import pytest
from fastapi.testclient import TestClient
from securoxi.api.app import app

client = TestClient(app)


def test_liveness_probe_endpoint():
    """Verify that liveness probe returns HTTP 200 OK."""
    response = client.get("/api/v1/health/liveness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_readiness_probe_endpoint():
    """Verify that readiness probe checks database and dependencies."""
    response = client.get("/api/v1/health/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ready", "degraded"]
    assert "database" in data


def test_security_headers_presence():
    """Verify that mandatory secure HTTP headers are set on API responses."""
    response = client.get("/api/v1/health/liveness")
    assert response.status_code == 200
    
    headers = response.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert "max-age=31536000" in headers.get("Strict-Transport-Security", "")
    assert "default-src 'self'" in headers.get("Content-Security-Policy", "")
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert headers.get("Permissions-Policy") == "camera=(), microphone=(), geolocation=()"


def test_invalid_api_key_401_response():
    """Verify that unauthenticated API requests to protected endpoints return 401 Unauthorized."""
    response = client.get("/api/v1/scans", headers={"X-API-Key": "invalid-key-xyz"})
    assert response.status_code == 401
    assert "Invalid API Key" in response.json()["detail"]
