"""
SECUROXI AI Intelligence 2.0 — Hiring & Screening Agent Types & Enums
Defines candidate qualification states, requirement types, evidence tiers, and ATS action enums.
"""

from enum import Enum


class CandidateQualificationState(str, Enum):
    """Normalized qualification and triage state for a screened candidate."""
    QUALIFIED = "QUALIFIED"
    NEAR_MATCH = "NEAR_MATCH"
    REVIEW = "REVIEW"
    QUARANTINED = "QUARANTINED"
    UNINSPECTABLE = "UNINSPECTABLE"
    FAILED = "FAILED"


class RequirementType(str, Enum):
    """Categorization of JD requirements and screening criteria."""
    MANDATORY = "MANDATORY"
    PREFERRED = "PREFERRED"
    EXCLUSION = "EXCLUSION"
    FILTER = "FILTER"
    RANKING_SIGNAL = "RANKING_SIGNAL"


class EvidenceQualityTier(str, Enum):
    """Granular verification state of candidate skill and experience evidence."""
    VERIFIED = "VERIFIED"
    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"
    CONFLICTING = "CONFLICTING"
    UNKNOWN = "UNKNOWN"


class ATSOperationType(str, Enum):
    """Operations proposed or executed against connected ATS providers."""
    SYNC_CANDIDATES = "SYNC_CANDIDATES"
    ADVANCE_CANDIDATE = "ADVANCE_CANDIDATE"
    REJECT_CANDIDATE = "REJECT_CANDIDATE"
    TAG_CANDIDATE = "TAG_CANDIDATE"
