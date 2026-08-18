"""
SECUROXI AI Intelligence 2.0 — Retrieval & Research Agent Types & Enums
Defines retrieval strategies, evidence sufficiency tiers, and research result types.
"""

from enum import Enum


class RetrievalStrategy(str, Enum):
    """Execution strategy applied during document and chunk retrieval."""
    SEMANTIC_VECTOR = "SEMANTIC_VECTOR"
    KEYWORD_EXACT = "KEYWORD_EXACT"
    HYBRID = "HYBRID"
    METADATA_FILTERED = "METADATA_FILTERED"


class EvidenceSufficiencyState(str, Enum):
    """Grounded evaluation of whether retrieved evidence satisfies the query requirements."""
    SUFFICIENT = "SUFFICIENT"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    INSUFFICIENT = "INSUFFICIENT"
    CONFLICTING = "CONFLICTING"
    NOT_FOUND = "NOT_FOUND"


class ResearchResultType(str, Enum):
    """Categorization of research output format produced for downstream consumption."""
    ANSWER_SUPPORT = "ANSWER_SUPPORT"
    CANDIDATE_SET = "CANDIDATE_SET"
    DOCUMENT_SET = "DOCUMENT_SET"
    COMPARISON_SET = "COMPARISON_SET"
    EVIDENCE_ONLY = "EVIDENCE_ONLY"
    RESEARCH_CONTEXT = "RESEARCH_CONTEXT"
