"""
SECUROXI AI Intelligence 2.0 — Enterprise Partner Ecosystem Types & Enums (Phase 9 Stage 60)
"""

from enum import Enum


class PartnerType(str, Enum):
    TECHNOLOGY_PARTNER = "TECHNOLOGY_PARTNER"
    IMPLEMENTATION_PARTNER = "IMPLEMENTATION_PARTNER"
    INTEGRATION_PARTNER = "INTEGRATION_PARTNER"
    SOLUTION_PARTNER = "SOLUTION_PARTNER"
    INTERNAL_PLATFORM_TEAM = "INTERNAL_PLATFORM_TEAM"


class PartnerVerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    APPROVED = "APPROVED"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


class DelegationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class PartnerScope(str, Enum):
    API_READ = "api.read"
    API_WRITE = "api.write"
    EVENTS_SUBSCRIBE = "events.subscribe"
    WORKFLOW_READ = "workflow.read"
    WORKFLOW_CREATE = "workflow.create"
    CAPABILITY_PUBLISH = "capability.publish"
    MARKETPLACE_PUBLISH = "marketplace.publish"
    INTEGRATION_MANAGE = "integration.manage"
