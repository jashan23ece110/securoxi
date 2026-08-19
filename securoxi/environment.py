"""
SECUROXI AI Intelligence 2.0 — Production Deployment Environment & Configuration Hardening (Stage 25)
Centralized, validated environment configuration for Development, Staging, and Production.
Enforces secret isolation, database connection policies, CORS allowlists, and startup health validation.
"""

import os
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field

from securoxi.logger import get_logger

logger = get_logger("securoxi.environment")


class EnvironmentMode(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ProductionDeploymentConfig(BaseModel):
    """Authoritative production deployment settings."""
    environment: EnvironmentMode = EnvironmentMode.DEVELOPMENT
    api_key: str = Field(default="securoxi-enterprise-key")
    database_url: str = Field(default="sqlite:///securoxi.db")
    storage_root: str = Field(default="./data/storage")
    cors_allowed_origins: List[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://localhost:8000", "http://127.0.0.1:8000"])
    max_upload_size_bytes: int = Field(default=15 * 1024 * 1024)  # 15 MB
    rate_limit_per_minute: int = Field(default=120)
    ai_provider: str = Field(default="mock")
    gemini_api_key: Optional[str] = None
    enable_detailed_telemetry: bool = Field(default=True)


def load_deployment_config() -> ProductionDeploymentConfig:
    """Loads and normalizes deployment configuration from environment variables."""
    env_str = os.environ.get("ENVIRONMENT", "development").lower()
    env_mode = EnvironmentMode(env_str) if env_str in EnvironmentMode.__members__ else EnvironmentMode.DEVELOPMENT

    # Parse CORS origins
    cors_raw = os.environ.get("CORS_ALLOWED_ORIGINS", "")
    if cors_raw:
        origins = [o.strip() for o in cors_raw.split(",") if o.strip()]
    else:
        if env_mode == EnvironmentMode.PRODUCTION:
            origins = ["https://app.securoxi.ai", "https://securoxi.ai"]
        elif env_mode == EnvironmentMode.STAGING:
            origins = ["https://staging.securoxi.ai"]
        else:
            origins = ["http://localhost:5173", "http://localhost:8000", "http://127.0.0.1:8000"]

    cfg = ProductionDeploymentConfig(
        environment=env_mode,
        api_key=os.environ.get("SECUROXI_API_KEY", "securoxi-enterprise-key"),
        database_url=os.environ.get("DATABASE_URL", "sqlite:///securoxi.db"),
        storage_root=os.environ.get("STORAGE_ROOT", "./data/storage"),
        cors_allowed_origins=origins,
        max_upload_size_bytes=int(os.environ.get("MAX_UPLOAD_SIZE_BYTES", str(15 * 1024 * 1024))),
        rate_limit_per_minute=int(os.environ.get("RATE_LIMIT_PER_MINUTE", "120")),
        ai_provider=os.environ.get("AI_PROVIDER", "mock"),
        gemini_api_key=os.environ.get("GEMINI_API_KEY"),
        enable_detailed_telemetry=os.environ.get("ENABLE_DETAILED_TELEMETRY", "true").lower() == "true",
    )
    return cfg


def validate_environment(config: Optional[ProductionDeploymentConfig] = None) -> List[str]:
    """
    Validates deployment environment and returns any configuration warnings or errors.
    In PRODUCTION mode, insecure default keys or wildcard CORS are strictly prohibited.
    """
    cfg = config or load_deployment_config()
    issues: List[str] = []

    if cfg.environment == EnvironmentMode.PRODUCTION:
        if cfg.api_key == "securoxi-enterprise-key":
            issues.append("PRODUCTION_INSECURE_DEFAULT_API_KEY: Default API key cannot be used in production.")
        if "*" in cfg.cors_allowed_origins:
            issues.append("PRODUCTION_INSECURE_CORS: Wildcard CORS origin is forbidden in production.")
        if cfg.ai_provider == "gemini" and not cfg.gemini_api_key:
            issues.append("PRODUCTION_MISSING_AI_KEY: GEMINI_API_KEY is required when AI_PROVIDER is 'gemini'.")

    # Storage path validation
    try:
        os.makedirs(cfg.storage_root, exist_ok=True)
    except Exception as e:
        issues.append(f"STORAGE_ROOT_INACCESSIBLE: Cannot write to storage path '{cfg.storage_root}': {e}")

    return issues
