"""
SECUROXI AI Intelligence 2.0 — Forensic Agent Types & Enums
Defines forensic finding statuses, evidence sufficiency tiers, and investigation states.
"""

from enum import Enum


class ForensicFindingStatus(str, Enum):
    """Observation and correlation classification of a forensic finding."""
    OBSERVED = "OBSERVED"
    CORRELATED = "CORRELATED"
    INFERRED = "INFERRED"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class EvidenceSufficiencyTier(str, Enum):
    """Sufficiency evaluation of forensic evidence supporting an investigated threat."""
    SUFFICIENT = "SUFFICIENT"
    PARTIAL = "PARTIAL"
    INSUFFICIENT = "INSUFFICIENT"
    CONFLICTING = "CONFLICTING"
