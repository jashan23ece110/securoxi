"""
SECUROXI AI Intelligence 2.0 — Custom Agent, Skill & Tool Platform Types (Phase 9 Stage 56)
"""

from enum import Enum


class CapabilityType(str, Enum):
    CUSTOM_AGENT = "CUSTOM_AGENT"
    CUSTOM_SKILL = "CUSTOM_SKILL"
    CUSTOM_TOOL = "CUSTOM_TOOL"
    CUSTOM_CONNECTOR = "CUSTOM_CONNECTOR"


class CapabilityStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    SECURITY_REVIEW = "SECURITY_REVIEW"
    EVALUATION = "EVALUATION"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    REVOKED = "REVOKED"
    DEPRECATED = "DEPRECATED"


class ToolRiskClass(str, Enum):
    READ_ONLY = "READ_ONLY"
    LOW_IMPACT = "LOW_IMPACT"
    MODERATE = "MODERATE"
    HIGH_IMPACT = "HIGH_IMPACT"
    CRITICAL = "CRITICAL"


class DeploymentMode(str, Enum):
    DRAFT = "DRAFT"
    TEST = "TEST"
    STAGING = "STAGING"
    CANARY = "CANARY"
    PRODUCTION = "PRODUCTION"
