"""
SECUROXI AI Intelligence 2.0 — Cross-Document Reasoning & Research Synthesis Types
Defines synthesis execution modes, comparison dimensions, and completion statuses.
"""

from enum import Enum


class SynthesisMode(str, Enum):
    """Execution mode and structure profile for cross-document synthesis."""
    DIRECT_ANSWER = "DIRECT_ANSWER"
    SUMMARY = "SUMMARY"
    COMPARISON = "COMPARISON"
    RANKING_EXPLANATION = "RANKING_EXPLANATION"
    RESEARCH = "RESEARCH"
    CROSS_DOCUMENT_ANALYSIS = "CROSS_DOCUMENT_ANALYSIS"
    GAP_ANALYSIS = "GAP_ANALYSIS"
    SECURITY_EXPLANATION = "SECURITY_EXPLANATION"
    INCIDENT_SUMMARY = "INCIDENT_SUMMARY"
    HIRING_RECOMMENDATION = "HIRING_RECOMMENDATION"
    REPORT = "REPORT"


class ComparisonDimension(str, Enum):
    """Standardized dimensions for structured cross-document and entity comparisons."""
    SECURITY_STATUS = "SECURITY_STATUS"
    CORE_QUALIFICATIONS = "CORE_QUALIFICATIONS"
    YEARS_EXPERIENCE = "YEARS_EXPERIENCE"
    FIT_SCORE = "FIT_SCORE"
    EVIDENCE_STRENGTH = "EVIDENCE_STRENGTH"


class SynthesisStatus(str, Enum):
    """Final operational status of the synthesized research outcome."""
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    CONFLICTING = "CONFLICTING"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    BLOCKED = "BLOCKED"
