"""
SECUROXI AI Production Secrets Management & Configuration Security Test Suite
Validates provider abstraction, secret masking (secu***), production startup validation,
key rotation, and environment separation.
"""

import os
import pytest
from securoxi.secrets import (
    SecretProvider,
    EnvironmentSecretProvider,
    ProductionSecretProvider,
    SecuroxiSecretsManager,
    mask_secret
)


def test_secret_masking_utility():
    """Verify that secret masking obfuscates sensitive key strings cleanly."""
    assert mask_secret("securoxi-enterprise-key", visible_chars=4) == "secu***"
    assert mask_secret("short", visible_chars=4) == "shor***"
    assert mask_secret("", visible_chars=4) == "[NOT_SET]"
    assert mask_secret(None, visible_chars=4) == "[NOT_SET]"


def test_environment_secret_provider(monkeypatch):
    """Verify EnvironmentSecretProvider reads environment variables."""
    monkeypatch.setenv("TEST_SECRET_KEY", "secret-val-123")
    provider = EnvironmentSecretProvider()
    assert provider.get_secret("TEST_SECRET_KEY") == "secret-val-123"
    assert provider.get_secret("NON_EXISTENT_KEY", default="default-val") == "default-val"


def test_production_secret_provider():
    """Verify ProductionSecretProvider reads from vault cache or secrets dictionary."""
    cache = {"SECUROXI_API_KEY": "vault-key-abc-789"}
    provider = ProductionSecretProvider(secrets_dict=cache)
    assert provider.get_secret("SECUROXI_API_KEY") == "vault-key-abc-789"


def test_production_startup_validation_rejects_default_dev_key(monkeypatch):
    """Verify production startup fails safely if SECUROXI_API_KEY uses default dev key."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECUROXI_API_KEY", "securoxi-enterprise-key")
    
    mgr = SecuroxiSecretsManager()
    with pytest.raises(ValueError, match="Production configuration failure"):
        mgr.validate_production_configuration()


def test_production_startup_validation_passes_with_secure_key(monkeypatch):
    """Verify production startup passes cleanly when a non-default production API key is provided."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECUROXI_API_KEY", "prod_live_securoxi_8971239128391283")
    
    mgr = SecuroxiSecretsManager()
    assert mgr.validate_production_configuration() is True


def test_secret_key_rotation_workflow():
    """Verify secret manager supports key rotation without application code modification."""
    old_cache = {"SECUROXI_API_KEY": "old-key-1"}
    new_cache = {"SECUROXI_API_KEY": "new-rotated-key-2"}

    provider_v1 = ProductionSecretProvider(secrets_dict=old_cache)
    mgr1 = SecuroxiSecretsManager(provider=provider_v1)
    assert mgr1.get_api_key() == "old-key-1"

    provider_v2 = ProductionSecretProvider(secrets_dict=new_cache)
    mgr2 = SecuroxiSecretsManager(provider=provider_v2)
    assert mgr2.get_api_key() == "new-rotated-key-2"
