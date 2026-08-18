"""
SECUROXI AI Intelligence 2.0 — Incident Agent Types & Enums
Defines incident severity classifications and response recommendation types.
"""

from enum import Enum


class IncidentTriageSeverity(str, Enum):
    """Normalized incident severity level."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentRecommendationType(str, Enum):
    """Categorization of proposed incident response actions."""
    INVESTIGATE_FURTHER = "INVESTIGATE_FURTHER"
    REVIEW_DOCUMENT = "REVIEW_DOCUMENT"
    QUARANTINE = "QUARANTINE"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"
    REQUEST_APPROVAL = "REQUEST_APPROVAL"
    RESOLVE = "RESOLVE"
