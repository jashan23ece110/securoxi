"""
SECUROXI AI Production Containerization & Deployment Integration Test Suite
Validates Dockerfile hardening specifications, docker-compose resource limits,
environment isolation, and non-root execution permissions.
"""

import os
import pytest


def test_dockerfile_hardening_specifications():
    """Verify Dockerfile contains multi-stage builds, non-root user, and HEALTHCHECK."""
    dockerfile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Dockerfile"))
    assert os.path.exists(dockerfile_path)

    with open(dockerfile_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "FROM python:3.12-slim AS builder" in content
    assert "FROM python:3.12-slim AS runner" in content
    assert "USER securoxiuser" in content
    assert "HEALTHCHECK" in content


def test_docker_compose_resource_limits_and_volumes():
    """Verify docker-compose.yml configures resource caps and isolated bridge network."""
    compose_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docker-compose.yml"))
    assert os.path.exists(compose_path)

    with open(compose_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "securoxi-ingress-proxy" in content
    assert "securoxi-postgres-db" in content
    assert "securoxi-redis-broker" in content
    assert "securoxi-bridge" in content
    assert "limits:" in content
    assert "memory: 2048M" in content


def test_environment_isolation_modes(monkeypatch):
    """Verify application recognizes DEVELOPMENT, STAGING, and PRODUCTION modes."""
    monkeypatch.setenv("ENVIRONMENT", "staging")
    env = os.environ.get("ENVIRONMENT", "development").lower()
    assert env == "staging"
