"""
SECUROXI AI Intelligence 2.0 — Query & Retrieval Complexity Classifier
Classifies retrieval objectives into SIMPLE, MODERATE, COMPLEX, MULTI_HOP, or RESEARCH
based on syntactic, semantic, boolean, and entity constraints.
"""

from typing import Dict, Any, Optional
from securoxi.orchestrator.retrieval_planner.types import RetrievalComplexity
from securoxi.logger import get_logger

logger = get_logger("orchestrator.retrieval_classifier")


class RetrievalComplexityClassifier:
    """Classifies queries and research objectives into calibrated complexity tiers."""

    def classify(self, query: str, context: Optional[Dict[str, Any]] = None) -> RetrievalComplexity:
        """
        Deterministically evaluates query characteristics:
        - Word count and multi-clause indicators
        - Entity counts and boolean operators ('and', 'or', 'not')
        - Comparative and aggregative keywords ('compare', 'explain why', 'top', 'across all')
        - Multi-hop requirements ('first find... then verify...')
        """
        q = (query or "").lower().strip()
        params = context or {}

        # 1. Research / Multi-Hop detection
        if any(term in q for term in ["deep research", "comprehensive audit", "across all tenants", "across all documents", "compare and contrast", "why is", "explain why"]):
            return RetrievalComplexity.RESEARCH

        if any(term in q for term in ["then verify", "followed by", "cross-reference", "multi-hop", "correlate with"]):
            return RetrievalComplexity.MULTI_HOP

        # 2. Complex Queries (multiple conditions, comparisons, top N with criteria)
        num_conditions = sum(1 for word in [" and ", " with ", " meeting ", " requiring ", " years ", " experience "] if word in q)
        if ("top " in q and num_conditions >= 2) or ("compare" in q) or num_conditions >= 3:
            return RetrievalComplexity.COMPLEX

        # 3. Moderate Queries (dual criteria, entity + security constraint)
        if num_conditions >= 1 or "safe" in q or "security" in q or len(q.split()) > 6:
            return RetrievalComplexity.MODERATE

        # 4. Simple Lookup
        return RetrievalComplexity.SIMPLE
