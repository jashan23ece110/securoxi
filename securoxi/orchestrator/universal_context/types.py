"""
SECUROXI AI Intelligence 2.0 — Universal Input & Context Types (Phase 4 Stage 17)
Strongly typed enumerations for context items, sources, security, trust, and relationships.
"""

from enum import Enum


class ContextItemType(str, Enum):
    """Supported types of items that can be attached to a UniversalTaskContext."""
    FILE = "FILE"
    DOCUMENT = "DOCUMENT"
    FOLDER = "FOLDER"
    COLLECTION = "COLLECTION"
    JOB_DESCRIPTION = "JOB_DESCRIPTION"
    CANDIDATE = "CANDIDATE"
    CANDIDATE_POOL = "CANDIDATE_POOL"
    ATS_JOB = "ATS_JOB"
    ATS_CANDIDATE = "ATS_CANDIDATE"
    INCIDENT = "INCIDENT"
    FINDING = "FINDING"
    POLICY = "POLICY"
    PREVIOUS_TASK_RESULT = "PREVIOUS_TASK_RESULT"


class ContextSourceType(str, Enum):
    """Origin of a context item."""
    LOCAL_UPLOAD = "LOCAL_UPLOAD"
    LOCAL_FOLDER = "LOCAL_FOLDER"
    ATS = "ATS"
    INDEXED_COLLECTION = "INDEXED_COLLECTION"
    EXISTING_DOCUMENT = "EXISTING_DOCUMENT"
    USER_SELECTION = "USER_SELECTION"
    PREVIOUS_TASK = "PREVIOUS_TASK"
    SYSTEM_SOURCE = "SYSTEM_SOURCE"


class ContextScope(str, Enum):
    """Authorization and operational boundary of a context item."""
    TASK = "TASK"
    DOCUMENT = "DOCUMENT"
    FOLDER = "FOLDER"
    COLLECTION = "COLLECTION"
    JOB = "JOB"
    CANDIDATE = "CANDIDATE"
    INCIDENT = "INCIDENT"
    TENANT = "TENANT"


class ContextSecurityState(str, Enum):
    """Deterministic security verdict of a context item."""
    SAFE = "SAFE"
    SUSPICIOUS = "SUSPICIOUS"
    HIGH_RISK = "HIGH_RISK"
    UNINSPECTABLE = "UNINSPECTABLE"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class ContextTrustLevel(str, Enum):
    """Workflow trust level, decoupled from raw security state."""
    TRUSTED_CONTEXT = "TRUSTED_CONTEXT"
    RESTRICTED_CONTEXT = "RESTRICTED_CONTEXT"
    UNTRUSTED_EVIDENCE = "UNTRUSTED_EVIDENCE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class RelationshipType(str, Enum):
    """Explicit, machine-readable relationship between context items."""
    APPLIES_TO = "APPLIES_TO"
    CONTAINS = "CONTAINS"
    REPRESENTED_BY = "REPRESENTED_BY"
    DERIVED_FROM = "DERIVED_FROM"
    REFERENCES = "REFERENCES"
    CONFLICTS_WITH = "CONFLICTS_WITH"


class ContextStatus(str, Enum):
    """Lifecycle status of a UniversalTaskContext."""
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    EXPIRED = "EXPIRED"
    INVALID = "INVALID"
