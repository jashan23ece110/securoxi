"""
SECUROXI AI Intelligence 2.0 — Adaptive Retrieval Execution Types & Enums
Defines hop classifications, evidence gap types, adaptive next-step decisions,
quality states, and stop reasons for multi-hop retrieval.
"""

from enum import Enum


class RetrievalHopType(str, Enum):
    """Classification of an individual multi-hop retrieval step."""
    ROOT_HOP = "ROOT_HOP"
    FOLLOW_UP_HOP = "FOLLOW_UP_HOP"
    EXPANSION_HOP = "EXPANSION_HOP"
    VERIFICATION_HOP = "VERIFICATION_HOP"
    COMPARISON_HOP = "COMPARISON_HOP"


class EvidenceGapType(str, Enum):
    """Categorization of missing evidence preventing task resolution."""
    MISSING_ENTITY = "MISSING_ENTITY"
    MISSING_ATTRIBUTE = "MISSING_ATTRIBUTE"
    MISSING_CONTEXT = "MISSING_CONTEXT"
    MISSING_SOURCE = "MISSING_SOURCE"
    MISSING_CITATION = "MISSING_CITATION"
    INSUFFICIENT_COVERAGE = "INSUFFICIENT_COVERAGE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    SECURITY_STATUS_UNKNOWN = "SECURITY_STATUS_UNKNOWN"
    TEMPORAL_GAP = "TEMPORAL_GAP"
    SCOPE_GAP = "SCOPE_GAP"


class NextHopDecision(str, Enum):
    """Deterministic decision determining the subsequent adaptive retrieval action."""
    CONTINUE = "CONTINUE"
    REQUERY = "REQUERY"
    EXPAND = "EXPAND"
    SWITCH_SOURCE = "SWITCH_SOURCE"
    RERANK = "RERANK"
    VERIFY = "VERIFY"
    COMPARE = "COMPARE"
    STOP = "STOP"
    ESCALATE = "ESCALATE"
    ABORT = "ABORT"


class RetrievalQualityState(str, Enum):
    """Normalized terminal quality state of the synthesized retrieval outcome."""
    SUFFICIENT = "SUFFICIENT"
    PARTIAL = "PARTIAL"
    INSUFFICIENT = "INSUFFICIENT"
    CONFLICTING = "CONFLICTING"
    NOT_FOUND = "NOT_FOUND"
    UNAVAILABLE = "UNAVAILABLE"


class StopReason(str, Enum):
    """Explicit rationale for terminating the adaptive retrieval loop."""
    EVIDENCE_SUFFICIENT = "EVIDENCE_SUFFICIENT"
    TOP_K_REACHED = "TOP_K_REACHED"
    MAX_ITERATIONS = "MAX_ITERATIONS"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    NO_NEW_INFORMATION = "NO_NEW_INFORMATION"
    CONFLICT_REQUIRES_REVIEW = "CONFLICT_REQUIRES_REVIEW"
    SECURITY_BLOCKED = "SECURITY_BLOCKED"
    RETRIEVAL_UNAVAILABLE = "RETRIEVAL_UNAVAILABLE"
