"""
SECUROXI AI Intelligence 2.0 — Cross-Organization Benchmarking Types & Enums (Phase 9 Stage 58)
"""

from enum import Enum


class ParticipationState(str, Enum):
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    OPTED_OUT = "OPTED_OUT"
    ELIGIBLE = "ELIGIBLE"
    PARTICIPATING = "PARTICIPATING"
    SUSPENDED = "SUSPENDED"


class BenchmarkDomain(str, Enum):
    SECURITY = "SECURITY"
    HIRING = "HIRING"
    WORKFLOW_OPERATIONS = "WORKFLOW_OPERATIONS"
    AGENTIC_RAG = "AGENTIC_RAG"
    AUTONOMY_GOVERNANCE = "AUTONOMY_GOVERNANCE"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class CohortDimension(str, Enum):
    ORG_SIZE = "ORG_SIZE"
    WORKFLOW_VOLUME = "WORKFLOW_VOLUME"
    DEPLOYMENT_TYPE = "DEPLOYMENT_TYPE"
