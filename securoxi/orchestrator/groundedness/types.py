"""
SECUROXI AI Intelligence 2.0 — Groundedness Verification Types & Enums
Defines claim classifications, evidence support states, groundedness states,
answer statuses, and conflict resolution strategies.
"""

from enum import Enum


class ClaimType(str, Enum):
    """Categorization of extracted atomic claims for targeted verification."""
    FACTUAL = "FACTUAL"
    COMPARATIVE = "COMPARATIVE"
    RANKING = "RANKING"
    SECURITY = "SECURITY"
    POLICY = "POLICY"
    QUALIFICATION = "QUALIFICATION"
    SUMMARY = "SUMMARY"
    AGGREGATION = "AGGREGATION"
    TEMPORAL = "TEMPORAL"
    CAUSAL = "CAUSAL"
    RECOMMENDATION = "RECOMMENDATION"


class EvidenceSupportState(str, Enum):
    """Grounded classification of support between claim and authoritative evidence."""
    DIRECTLY_SUPPORTED = "DIRECTLY_SUPPORTED"
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    WEAKLY_SUPPORTED = "WEAKLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNVERIFIABLE = "UNVERIFIABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class GroundednessState(str, Enum):
    """Composite groundedness classification of the synthesized claim set."""
    FULLY_GROUNDED = "FULLY_GROUNDED"
    MOSTLY_GROUNDED = "MOSTLY_GROUNDED"
    PARTIALLY_GROUNDED = "PARTIALLY_GROUNDED"
    INSUFFICIENTLY_GROUNDED = "INSUFFICIENTLY_GROUNDED"
    UNGROUNDED = "UNGROUNDED"


class AnswerStatus(str, Enum):
    """Final answer status determining publishability and qualification level."""
    GROUNDED = "GROUNDED"
    GROUNDED_WITH_QUALIFICATIONS = "GROUNDED_WITH_QUALIFICATIONS"
    PARTIAL = "PARTIAL"
    CONFLICTING = "CONFLICTING"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


class ConflictResolutionStrategy(str, Enum):
    """Deterministic method used to arbitrate contradictory evidence."""
    RESOLVED_BY_AUTHORITY = "RESOLVED_BY_AUTHORITY"
    RESOLVED_BY_RECENCY = "RESOLVED_BY_RECENCY"
    UNRESOLVED_CONFLICT = "UNRESOLVED_CONFLICT"
