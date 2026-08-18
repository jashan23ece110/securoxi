"""
SECUROXI AI Intelligence 2.0 — Evidence Fusion & Advanced Reranking Types
Defines source authority classifications, evidence quality tiers,
score normalization methods, and requirement coverage states.
"""

from enum import Enum


class EvidenceSourceType(str, Enum):
    """Source authority classification ranking reliability and provenance."""
    DETERMINISTIC_SECURITY = "DETERMINISTIC_SECURITY"
    ATS_METADATA = "ATS_METADATA"
    OFFICIAL_JD = "OFFICIAL_JD"
    CANDIDATE_RESUME = "CANDIDATE_RESUME"
    ENTERPRISE_DOC = "ENTERPRISE_DOC"
    DERIVED_SUMMARY = "DERIVED_SUMMARY"
    LLM_ADVISORY = "LLM_ADVISORY"


class EvidenceQualityTier(str, Enum):
    """Calibrated quality classification of fused evidence."""
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    SUPPORTED = "SUPPORTED"
    INSUFFICIENT = "INSUFFICIENT"
    CONFLICTING = "CONFLICTING"
    UNTRUSTED = "UNTRUSTED"


class ScoreNormalizationMethod(str, Enum):
    """Score normalization algorithm across heterogeneous retrieval methods."""
    MIN_MAX = "MIN_MAX"
    Z_SCORE = "Z_SCORE"
    RANK_BASED = "RANK_BASED"
    RECIPROCAL_RANK_FUSION = "RECIPROCAL_RANK_FUSION"


class CoverageState(str, Enum):
    """Coverage state for individual evidence requirements."""
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"
    CONFLICTING = "CONFLICTING"
