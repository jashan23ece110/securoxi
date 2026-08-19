"""
SECUROXI AI Intelligence 2.0 — Enterprise ATS Integrations Enums & Types
"""

from enum import Enum


class ATSProviderType(str, Enum):
    GREENHOUSE = "GREENHOUSE"
    LEVER = "LEVER"
    WORKDAY = "WORKDAY"
    MOCK = "MOCK"


class IntegrationStatus(str, Enum):
    CONNECTED = "CONNECTED"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    DEGRADED = "DEGRADED"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"
    DISABLED = "DISABLED"


class IntegrationCapability(str, Enum):
    READ_JOBS = "READ_JOBS"
    READ_CANDIDATES = "READ_CANDIDATES"
    READ_RESUMES = "READ_RESUMES"
    WRITE_STAGE = "WRITE_STAGE"
    WRITE_NOTES = "WRITE_NOTES"


class SyncStatus(str, Enum):
    IDLE = "IDLE"
    SYNCING = "SYNCING"
    SYNCED = "SYNCED"
    PARTIAL_SYNC = "PARTIAL_SYNC"
    FAILED = "FAILED"
