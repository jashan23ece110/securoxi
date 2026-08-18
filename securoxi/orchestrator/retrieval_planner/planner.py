"""
SECUROXI AI Intelligence 2.0 — Agentic Retrieval Planner & Strategy Selector
Dynamically selects retrieval strategies, decomposes compound queries, formulates
evidence requirements, injects security filters, and generates validated RetrievalPlans.
"""

from typing import Dict, Any, List, Optional, Tuple
import re
from securoxi.orchestrator.retrieval_planner.types import (
    RetrievalStrategyType,
    RetrievalComplexity,
    RetrievalDepth,
    RetrievalLatencyMode,
    RetrievalStopCondition,
    QueryRewritePurpose,
)
from securoxi.orchestrator.retrieval_planner.models import (
    RetrievalQuerySpec,
    EvidenceRequirement,
    RetrievalPlan,
    RetrievalStrategyDecision,
)
from securoxi.orchestrator.retrieval_planner.classifier import RetrievalComplexityClassifier
from securoxi.orchestrator.retrieval_planner.validator import RetrievalPlanValidator
from securoxi.logger import get_logger

logger = get_logger("orchestrator.retrieval_planner")


class AgenticRetrievalPlanner:
    """
    Intelligent Planner deciding the optimal multi-strategy retrieval architecture
    for complex queries, cross-document analysis, and hiring security investigations.
    """

    def __init__(
        self,
        classifier: Optional[RetrievalComplexityClassifier] = None,
        validator: Optional[RetrievalPlanValidator] = None,
    ):
        self.classifier = classifier or RetrievalComplexityClassifier()
        self.validator = validator or RetrievalPlanValidator()

    def plan_retrieval(
        self,
        objective: str,
        tenant_id: str,
        task_id: str = "TASK-DEFAULT",
        scope: Optional[List[str]] = None,
        security_override: Optional[str] = None,
        user_constraints: Optional[List[str]] = None,
        max_cost: float = 1.0,
    ) -> Tuple[RetrievalPlan, RetrievalStrategyDecision]:
        """
        Synthesizes a complete, validated RetrievalPlan and explainable StrategyDecision:
        1. Classifies query complexity.
        2. Selects retrieval strategies and depth.
        3. Decomposes query into structured query variants with rewrite purposes.
        4. Injects mandatory evidence requirements and security filters.
        5. Validates plan safety deterministically.
        """
        logger.info(f"Formulating Retrieval Plan for '{objective[:60]}...' (Tenant: {tenant_id})")

        # 1. Classify Complexity
        complexity = self.classifier.classify(objective)

        # 2. Determine Strategies & Depth
        strategies: List[RetrievalStrategyType] = []
        depth = RetrievalDepth.TOP_EVIDENCE
        latency_mode = RetrievalLatencyMode.BALANCED
        rerank = True

        if complexity == RetrievalComplexity.SIMPLE:
            strategies = [RetrievalStrategyType.KEYWORD, RetrievalStrategyType.VECTOR_SEMANTIC]
            depth = RetrievalDepth.SURFACE
            latency_mode = RetrievalLatencyMode.FAST
            rerank = False
        elif complexity == RetrievalComplexity.MODERATE:
            strategies = [RetrievalStrategyType.HYBRID, RetrievalStrategyType.METADATA_FILTER]
            depth = RetrievalDepth.TOP_EVIDENCE
            latency_mode = RetrievalLatencyMode.BALANCED
            rerank = True
        elif complexity in [RetrievalComplexity.COMPLEX, RetrievalComplexity.MULTI_HOP]:
            strategies = [
                RetrievalStrategyType.HYBRID,
                RetrievalStrategyType.METADATA_FILTER,
                RetrievalStrategyType.CROSS_DOCUMENT,
            ]
            depth = RetrievalDepth.DEEP
            latency_mode = RetrievalLatencyMode.DEEP
            rerank = True
        else:  # RESEARCH
            strategies = [
                RetrievalStrategyType.HYBRID,
                RetrievalStrategyType.METADATA_FILTER,
                RetrievalStrategyType.CROSS_DOCUMENT,
                RetrievalStrategyType.DEEP_RESEARCH,
            ]
            depth = RetrievalDepth.RESEARCH
            latency_mode = RetrievalLatencyMode.DEEP
            rerank = True

        # 3. Query Decomposition & Rewriting
        queries = self._generate_query_variants(objective, complexity)

        # 4. Evidence Requirements
        evidence_reqs = self._derive_evidence_requirements(objective, queries)

        # 5. Security Filters
        sec_status = security_override or "SAFE"
        security_filters = {
            "security_status": sec_status,
            "tenant_id": tenant_id,
        }

        # 6. Construct RetrievalPlan
        plan = RetrievalPlan(
            task_id=task_id,
            tenant_id=tenant_id,
            objective=objective,
            complexity=complexity,
            selected_strategies=strategies,
            queries=queries,
            authorized_sources=scope or ["DOCUMENTS", "RESUMES"],
            security_filters=security_filters,
            evidence_requirements=evidence_reqs,
            depth=depth,
            latency_mode=latency_mode,
            rerank_required=rerank,
            verification_required=True,
            max_documents=20 if depth == RetrievalDepth.SURFACE else (100 if depth == RetrievalDepth.DEEP else 50),
            max_chunks=50 if depth == RetrievalDepth.SURFACE else 200,
            max_iterations=2 if depth == RetrievalDepth.SURFACE else 5,
            budget_cost_limit=max_cost,
            stop_conditions=[
                RetrievalStopCondition.EVIDENCE_SUFFICIENT,
                RetrievalStopCondition.NO_NEW_INFORMATION,
                RetrievalStopCondition.MAX_ITERATIONS,
            ],
            parallel_groups=[[q.query_text for q in queries]],
        )

        # 7. Validate Plan
        self.validator.validate(plan, tenant_id)

        # 8. Decision Diagnostic Rationale
        decision = RetrievalStrategyDecision(
            query=objective,
            complexity=complexity,
            selected_strategy=strategies[0] if strategies else RetrievalStrategyType.HYBRID,
            hybrid_selected=RetrievalStrategyType.HYBRID in strategies,
            rerank_selected=rerank,
            reasoning=f"Classified as {complexity.value}. Allocated {len(strategies)} strategies with depth {depth.value} and rerank={rerank}.",
        )

        return plan, decision

    def _generate_query_variants(self, objective: str, complexity: RetrievalComplexity) -> List[RetrievalQuerySpec]:
        """Decomposes and rewrites queries preserving original intent."""
        variants: List[RetrievalQuerySpec] = []
        raw = objective.strip()

        # Primary Query
        variants.append(
            RetrievalQuerySpec(
                query_text=raw,
                purpose=QueryRewritePurpose.CLARIFY_CONTEXT,
                weight=1.0,
            )
        )

        # Extract technology / exact terms
        exact_terms = []
        for term in ["Kubernetes", "AWS", "Python", "Docker", "Security", "CI/CD", "Terraform", "GCP"]:
            if term.lower() in raw.lower():
                exact_terms.append(term)

        if exact_terms:
            variants.append(
                RetrievalQuerySpec(
                    query_text=" ".join(exact_terms),
                    purpose=QueryRewritePurpose.ADD_REQUIRED_TERM,
                    exact_terms=exact_terms,
                    weight=0.8,
                )
            )

        # For Complex/Multi-hop: Expand synonyms
        if complexity in [RetrievalComplexity.COMPLEX, RetrievalComplexity.MULTI_HOP, RetrievalComplexity.RESEARCH]:
            if "production" in raw.lower() or "senior" in raw.lower():
                variants.append(
                    RetrievalQuerySpec(
                        query_text=f"{raw} enterprise deployment architecture",
                        purpose=QueryRewritePurpose.EXPAND_SYNONYMS,
                        weight=0.6,
                    )
                )

        return variants

    def _derive_evidence_requirements(self, objective: str, queries: List[RetrievalQuerySpec]) -> List[EvidenceRequirement]:
        """Derives explicit evidence criteria needed to ground downstream decisions."""
        reqs = []
        topics = []
        for q in queries:
            for term in q.exact_terms:
                if term not in topics:
                    topics.append(term)
        if not topics:
            topics = [objective.split()[0] if objective.split() else "General"]

        for i, topic in enumerate(topics[:4]):
            reqs.append(
                EvidenceRequirement(
                    requirement_id=f"REQ-{i+1}",
                    topic=topic,
                    mandatory=True,
                    expected_source_types=["DOCUMENT", "RESUME"],
                    min_citations=1,
                )
            )
        return reqs
