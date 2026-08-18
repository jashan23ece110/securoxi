"""
SECUROXI AI Intelligence 2.0 — Agentic Retrieval Planner Types & Enums
Defines retrieval strategies, query complexity tiers, retrieval depths,
latency modes, rewrite purposes, and stopping conditions.
"""

from enum import Enum


class RetrievalStrategyType(str, Enum):
    """Execution strategy applied during document and chunk retrieval."""
    VECTOR_SEMANTIC = "VECTOR_SEMANTIC"
    KEYWORD = "KEYWORD"
    HYBRID = "HYBRID"
    METADATA_FILTER = "METADATA_FILTER"
    EXACT_MATCH = "EXACT_MATCH"
    DOCUMENT_SCOPED = "DOCUMENT_SCOPED"
    COLLECTION_SCOPED = "COLLECTION_SCOPED"
    CANDIDATE_SCOPED = "CANDIDATE_SCOPED"
    JD_SCOPED = "JD_SCOPED"
    SECURITY_FILTERED = "SECURITY_FILTERED"
    TEMPORAL = "TEMPORAL"
    CROSS_DOCUMENT = "CROSS_DOCUMENT"
    BROAD_RESEARCH = "BROAD_RESEARCH"
    DEEP_RESEARCH = "DEEP_RESEARCH"


class RetrievalComplexity(str, Enum):
    """Categorization of query and retrieval task difficulty."""
    SIMPLE = "SIMPLE"
    MODERATE = "MODERATE"
    COMPLEX = "COMPLEX"
    MULTI_HOP = "MULTI_HOP"
    RESEARCH = "RESEARCH"


class RetrievalDepth(str, Enum):
    """Depth of retrieval search and evidence aggregation."""
    SURFACE = "SURFACE"
    TOP_EVIDENCE = "TOP_EVIDENCE"
    DEEP = "DEEP"
    RESEARCH = "RESEARCH"


class RetrievalLatencyMode(str, Enum):
    """Latency optimization profile for retrieval execution."""
    FAST = "FAST"
    BALANCED = "BALANCED"
    DEEP = "DEEP"


class RetrievalStopCondition(str, Enum):
    """Deterministic terminal conditions for retrieval loops."""
    EVIDENCE_SUFFICIENT = "EVIDENCE_SUFFICIENT"
    TOP_K_REACHED = "TOP_K_REACHED"
    MAX_ITERATIONS = "MAX_ITERATIONS"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    NO_NEW_INFORMATION = "NO_NEW_INFORMATION"
    CONFLICT_REQUIRES_REVIEW = "CONFLICT_REQUIRES_REVIEW"


class QueryRewritePurpose(str, Enum):
    """Explicit justification for query rewriting and synonym expansion."""
    EXPAND_SYNONYMS = "EXPAND_SYNONYMS"
    CLARIFY_CONTEXT = "CLARIFY_CONTEXT"
    ADD_ENTITY = "ADD_ENTITY"
    ADD_REQUIRED_TERM = "ADD_REQUIRED_TERM"
    REMOVE_NOISE = "REMOVE_NOISE"
    NARROW_SCOPE = "NARROW_SCOPE"
