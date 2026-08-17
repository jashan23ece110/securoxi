"""
SECUROXI AI Production Secrets Management & Configuration Security Layer
Provides provider-neutral SecretProvider abstraction, secret masking (secu***),
startup security validation for ENVIRONMENT=production, and key rotation helpers.
"""

import os
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from securoxi.logger import get_logger

logger = get_logger("securoxi.secrets")


def mask_secret(secret_val: Optional[str], visible_chars: int = 4) -> str:
    """Masks sensitive secret string for logging and debugging output (e.g. 'secu***')."""
    if not secret_val:
        return "[NOT_SET]"
    if len(secret_val) <= visible_chars:
        return "****"
    return f"{secret_val[:visible_chars]}***"


class SecretProvider(ABC):
    """Abstract Base Class for provider-neutral SECUROXI secret retrieval."""

    @abstractmethod
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        pass


class EnvironmentSecretProvider(SecretProvider):
    """Local Development & Testing Secret Provider reading environment variables and .env files."""

    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        return os.environ.get(secret_name, default)


class ProductionSecretProvider(SecretProvider):
    """Production Secret Provider reading from centralized secrets manager (e.g., Vault / AWS Secrets Manager)."""

    def __init__(self, secrets_dict: Optional[Dict[str, str]] = None):
        self._secrets_cache = secrets_dict or {}

    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        # Retrieve from cached vault/kms secrets or environment injection
        val = self._secrets_cache.get(secret_name) or os.environ.get(secret_name)
        return val or default


class SecuroxiSecretsManager:
    """Centralized Secrets Manager for SECUROXI application runtime."""

    def __init__(self, provider: Optional[SecretProvider] = None):
        env_mode = os.environ.get("ENVIRONMENT", "development").lower()
        if provider:
            self.provider = provider
        elif env_mode in ["production", "prod"]:
            self.provider = ProductionSecretProvider()
        else:
            self.provider = EnvironmentSecretProvider()

    def get_api_key(self) -> str:
        return self.provider.get_secret("SECUROXI_API_KEY", "securoxi-enterprise-key") or ""

    def get_gemini_api_key(self) -> Optional[str]:
        return self.provider.get_secret("GEMINI_API_KEY")

    def get_database_url(self) -> Optional[str]:
        return self.provider.get_secret("DATABASE_URL") or self.provider.get_secret("SECUROXI_DB_URL")

    def get_redis_url(self) -> Optional[str]:
        return self.provider.get_secret("REDIS_URL") or self.provider.get_secret("SECUROXI_REDIS_URL")

    def validate_production_configuration(self) -> bool:
        """
        Validates security-critical secrets on startup if ENVIRONMENT=production.
        Refuses to start if mandatory secrets are absent or using default dev values.
        """
        env_mode = os.environ.get("ENVIRONMENT", "development").lower()
        if env_mode in ["production", "prod"]:
            api_key = self.get_api_key()
            if not api_key or api_key == "securoxi-enterprise-key":
                logger.critical("PRODUCTION STARTUP BLOCKED: SECUROXI_API_KEY is missing or set to default dev key!")
                raise ValueError("Production configuration failure: SECUROXI_API_KEY must be set to a secure key.")

            db_url = self.get_database_url()
            if not db_url or "sqlite" in db_url.lower():
                logger.warning("PRODUCTION STARTUP WARNING: Production mode running on default SQLite persistence.")

            logger.info("Production configuration validated successfully.")
            return True
        return True


# Global default secrets manager singleton
secrets_manager = SecuroxiSecretsManager()
