"""
SECUROXI AI Intelligence 2.0 — Enterprise Control Plane Types & Enums (Phase 9 Stage 54)
"""

from enum import Enum


class PolicyDomain(str, Enum):
    SECURITY = "SECURITY"
    ACCESS_RBAC = "ACCESS_RBAC"
    HIRING_ATS = "HIRING_ATS"
    DATA_GOVERNANCE = "DATA_GOVERNANCE"
    AUTONOMY = "AUTONOMY"
    INTEGRATION = "INTEGRATION"


class PolicyStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ROLLED_BACK = "ROLLED_BACK"
    DEPRECATED = "DEPRECATED"


class CapabilityStatus(str, Enum):
    REGISTERED = "REGISTERED"
    VALIDATED = "VALIDATED"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    REVOKED = "REVOKED"


class EvaluationGateState(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class ControlPlaneDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    SIMULATION_ONLY = "SIMULATION_ONLY"
