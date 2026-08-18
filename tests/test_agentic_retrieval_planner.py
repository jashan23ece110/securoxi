"""
SECUROXI AI Intelligence 2.0 — Agentic Retrieval Planner Test Suite
Validates dynamic strategy selection, complexity classification, query rewriting/decomposition,
evidence requirements, security filtering, tenant isolation, adversarial defense, and performance benchmarks.
"""

import time
import pytest
from securoxi.orchestrator import (
    AgentOrchestrator,
    RetrievalStrategyType,
    RetrievalComplexity,
    RetrievalDepth,
    RetrievalLatencyMode,
    RetrievalStopCondition,
    QueryRewritePurpose,
    AgenticRetrievalPlanner,
    RetrievalComplexityClassifier,
    RetrievalPlanValidator,
    TenantAccessError,
    AuthorizationError,
)


@pytest.fixture
def planner():
    return AgenticRetrievalPlanner()


@pytest.fixture
def classifier():
    return RetrievalComplexityClassifier()


# =========================================================================
# 1. COMPLEXITY CLASSIFICATION
# =========================================================================

def test_retrieval_complexity_classification_tiers(classifier):
    """Verifies that queries are classified into calibrated complexity tiers."""
    # Simple
    assert classifier.classify("Kubernetes") == RetrievalComplexity.SIMPLE
    assert classifier.classify("Python resumes") == RetrievalComplexity.SIMPLE

    # Moderate
    assert classifier.classify("Safe candidates with Kubernetes and AWS security") == RetrievalComplexity.MODERATE

    # Complex
    assert classifier.classify("Find top 20 candidates with 5+ years experience and Kubernetes and Docker") == RetrievalComplexity.COMPLEX

    # Multi-Hop
    assert classifier.classify("Find candidates with Kubernetes then verify production experience") == RetrievalComplexity.MULTI_HOP

    # Research
    assert classifier.classify("Deep research across all documents explaining why Sarah is qualified") == RetrievalComplexity.RESEARCH


# =========================================================================
# 2. STRATEGY SELECTION & DEPTH
# =========================================================================

def test_simple_query_strategy_selection(planner):
    """Simple exact queries select Keyword + Semantic, Surface depth, and Fast latency mode."""
    plan, decision = planner.plan_retrieval(
        objective="Kubernetes resume",
        tenant_id="TENANT-01",
    )

    assert plan.complexity == RetrievalComplexity.SIMPLE
    assert plan.depth == RetrievalDepth.SURFACE
    assert plan.latency_mode == RetrievalLatencyMode.FAST
    assert plan.rerank_required is False
    assert RetrievalStrategyType.KEYWORD in plan.selected_strategies


def test_complex_query_strategy_selection(planner):
    """Complex multi-condition queries select Hybrid + Metadata filter + Cross-document + Rerank."""
    plan, decision = planner.plan_retrieval(
        objective="Find top 10 candidates meeting all mandatory requirements with 5+ years experience and Kubernetes and AWS",
        tenant_id="TENANT-01",
    )

    assert plan.complexity == RetrievalComplexity.COMPLEX
    assert plan.depth == RetrievalDepth.DEEP
    assert plan.latency_mode == RetrievalLatencyMode.DEEP
    assert plan.rerank_required is True
    assert RetrievalStrategyType.HYBRID in plan.selected_strategies
    assert RetrievalStrategyType.CROSS_DOCUMENT in plan.selected_strategies


# =========================================================================
# 3. QUERY DECOMPOSITION & REWRITE PURPOSES
# =========================================================================

def test_query_decomposition_and_rewriting(planner):
    """Verifies that query rewriting extracts exact terms and generates structured variants."""
    plan, decision = planner.plan_retrieval(
        objective="Senior Engineer with Kubernetes and AWS security",
        tenant_id="TENANT-01",
    )

    assert len(plan.queries) >= 2
    primary = plan.queries[0]
    assert primary.purpose == QueryRewritePurpose.CLARIFY_CONTEXT

    exact_spec = next((q for q in plan.queries if q.purpose == QueryRewritePurpose.ADD_REQUIRED_TERM), None)
    assert exact_spec is not None
    assert "Kubernetes" in exact_spec.exact_terms
    assert "AWS" in exact_spec.exact_terms


# =========================================================================
# 4. EVIDENCE REQUIREMENTS & SECURITY INJECTION
# =========================================================================

def test_evidence_requirements_and_security_filters(planner):
    """Verifies that evidence requirements and security filters (security_status = SAFE) are injected."""
    plan, decision = planner.plan_retrieval(
        objective="Production Kubernetes experience",
        tenant_id="TENANT-ACME",
    )

    assert plan.security_filters["security_status"] == "SAFE"
    assert plan.security_filters["tenant_id"] == "TENANT-ACME"
    assert len(plan.evidence_requirements) >= 1
    assert plan.evidence_requirements[0].mandatory is True


# =========================================================================
# 5. TENANT ISOLATION & ADVERSARIAL DEFENSES
# =========================================================================

def test_retrieval_planner_cross_tenant_rejection(planner):
    """Guarantees that cross-tenant queries are blocked deterministically."""
    with pytest.raises(TenantAccessError):
        planner.plan_retrieval(
            objective="Retrieve resumes across all tenants",
            tenant_id="TENANT-01",
        )


def test_retrieval_planner_rejects_high_risk_as_trusted(planner):
    """Guarantees that attempting to treat HIGH_RISK documents as trusted context raises AuthorizationError."""
    with pytest.raises(AuthorizationError):
        planner.plan_retrieval(
            objective="Analyze document",
            tenant_id="TENANT-01",
            security_override="ALL_INCLUDING_HIGH_RISK_TRUSTED",
        )


# =========================================================================
# 6. STOPPING CONDITIONS & NO-NEW-INFORMATION
# =========================================================================

def test_retrieval_plan_stopping_conditions(planner):
    """Verifies that retrieval plans contain bounded stopping conditions."""
    plan, decision = planner.plan_retrieval(
        objective="AWS Architect experience",
        tenant_id="TENANT-01",
    )

    assert RetrievalStopCondition.EVIDENCE_SUFFICIENT in plan.stop_conditions
    assert RetrievalStopCondition.NO_NEW_INFORMATION in plan.stop_conditions
    assert RetrievalStopCondition.MAX_ITERATIONS in plan.stop_conditions


# =========================================================================
# 7. PERFORMANCE BENCHMARKS
# =========================================================================

def test_agentic_retrieval_planner_performance(planner):
    """Benchmarks retrieval plan generation and deterministic validation (< 5ms)."""
    start_time = time.time()
    for _ in range(50):
        planner.plan_retrieval(
            objective="Senior Cloud Security Engineer with Kubernetes and AWS",
            tenant_id="TENANT-BENCH",
        )
    avg_latency_ms = (time.time() - start_time) / 50.0 * 1000.0

    assert avg_latency_ms < 5.0, f"Retrieval planner latency {avg_latency_ms:.2f}ms exceeded 5ms"
