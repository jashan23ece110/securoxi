"""
SECUROXI AI Intelligence 2.0 — Enterprise Data Governance & Retention Types
"""

from enum import Enum


class DataClassification(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"
    CANDIDATE_DATA = "CANDIDATE_DATA"
    SECURITY_EVIDENCE = "SECURITY_EVIDENCE"
    AUDIT_DATA = "AUDIT_DATA"


class RetentionTrigger(str, Enum):
    CREATION_TIME = "CREATION_TIME"
    LAST_ACTIVITY = "LAST_ACTIVITY"
    TASK_COMPLETION = "TASK_COMPLETION"
    INCIDENT_RESOLUTION = "INCIDENT_RESOLUTION"


class RetentionState(str, Enum):
    ACTIVE = "ACTIVE"
    RETENTION_PENDING = "RETENTION_PENDING"
    EXPIRED = "EXPIRED"
    LEGAL_HOLD = "LEGAL_HOLD"
    DELETION_PENDING = "DELETION_PENDING"
    DELETED = "DELETED"
    ARCHIVED = "ARCHIVED"


class LegalHoldStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"


class ExportStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    EXPIRED = "EXPIRED"
    DELETED = "DELETED"
