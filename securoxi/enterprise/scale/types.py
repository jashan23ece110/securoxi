"""
SECUROXI AI Intelligence 2.0 — Enterprise Scale & Disaster Recovery Types
"""

from enum import Enum


class DataRegion(str, Enum):
    US_EAST = "US_EAST"
    US_WEST = "US_WEST"
    EU_WEST = "EU_WEST"
    AP_SOUTH = "AP_SOUTH"


class FailoverStatus(str, Enum):
    PRIMARY_HEALTHY = "PRIMARY_HEALTHY"
    FAILOVER_IN_PROGRESS = "FAILOVER_IN_PROGRESS"
    SECONDARY_ACTIVE = "SECONDARY_ACTIVE"
    RESTORE_COMPLETE = "RESTORE_COMPLETE"


class BackupStatus(str, Enum):
    COMPLETED = "COMPLETED"
    RESTORED = "RESTORED"
    FAILED = "FAILED"


class WorkerPoolType(str, Enum):
    GENERAL_ORCHESTRATION = "GENERAL_ORCHESTRATION"
    SECURITY_PARSING = "SECURITY_PARSING"
    HIRING_SCREENING = "HIRING_SCREENING"
    AGENTIC_RAG = "AGENTIC_RAG"
