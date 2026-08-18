"""
SECUROXI AI Intelligence 2.0 — Agentic Retrieval Planner Data Models
Defines strongly typed models for Retrieval Query Specs, Evidence Requirements,
Retrieval Plans, Strategy Decisions, and Strategy Execution Envelopes.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import uuid
import time
from securoxi.orchestrator.retrieval_planner.types import (
    RetrievalStrategyType,
    RetrievalComplexity,
    RetrievalDepth,
    RetrievalLatencyMode,
    RetrievalStopCondition,
    QueryRewritePurpose,
)


@dataclass
class RetrievalQuerySpec:
    """Individual retrieval query variant with explicit rewrite purpose."""
    query_text: str
    purpose: QueryRewritePurpose = QueryRewritePurpose.CLARIFY_CONTEXT
    target_entities: List[str] = field(default_factory=list)
    exact_terms: List[str] = field(default_factory=list)
    weight: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_text": self.query_text,
            "purpose": self.purpose.value,
            "target_entities": self.target_entities,
            "exact_terms": self.exact_terms,
            "weight": self.weight,
        }


@dataclass
class EvidenceRequirement:
    """Explicit evidence criteria required to justify a final grounded result."""
    requirement_id: str = field(default_factory=lambda: f"REQ-{uuid.uuid4().hex[:6].upper()}")
    topic: str = "general"
    mandatory: bool = True
    expected_source_types: List[str] = field(default_factory=lambda: ["DOCUMENT", "RESUME"])
    min_citations: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "topic": self.topic,
            "mandatory": self.mandatory,
            "expected_source_types": self.expected_source_types,
            "min_citations": self.min_citations,
        }


@dataclass
class RetrievalPlan:
    """Comprehensive, validated retrieval plan produced by the Agentic Retrieval Planner."""
    plan_id: str = field(default_factory=lambda: f"RPLAN-{uuid.uuid4().hex[:8].upper()}")
    task_id: str = "TASK-DEFAULT"
    tenant_id: str = "TENANT-DEFAULT"
    objective: str = ""
    complexity: RetrievalComplexity = RetrievalComplexity.SIMPLE
    selected_strategies: List[RetrievalStrategyType] = field(default_factory=lambda: [RetrievalStrategyType.HYBRID])
    queries: List[RetrievalQuerySpec] = field(default_factory=list)
    authorized_sources: List[str] = field(default_factory=lambda: ["DOCUMENTS"])
    security_filters: Dict[str, Any] = field(default_factory=lambda: {"security_status": "SAFE"})
    evidence_requirements: List[EvidenceRequirement] = field(default_factory=list)
    depth: RetrievalDepth = RetrievalDepth.TOP_EVIDENCE
    latency_mode: RetrievalLatencyMode = RetrievalLatencyMode.BALANCED
    rerank_required: bool = True
    verification_required: bool = True
    max_documents: int = 50
    max_chunks: int = 100
    max_iterations: int = 3
    budget_cost_limit: float = 1.0
    stop_conditions: List[RetrievalStopCondition] = field(
        default_factory=lambda: [
            RetrievalStopCondition.EVIDENCE_SUFFICIENT,
            RetrievalStopCondition.NO_NEW_INFORMATION,
            RetrievalStopCondition.MAX_ITERATIONS,
        ]
    )
    parallel_groups: List[List[str]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "task_id": self.task_id,
            "tenant_id": self.tenant_id,
            "objective": self.objective,
            "complexity": self.complexity.value,
            "selected_strategies": [s.value for s in self.selected_strategies],
            "queries": [q.to_dict() for q in self.queries],
            "authorized_sources": self.authorized_sources,
            "security_filters": self.security_filters,
            "evidence_requirements": [e.to_dict() for e in self.evidence_requirements],
            "depth": self.depth.value,
            "latency_mode": self.latency_mode.value,
            "rerank_required": self.rerank_required,
            "verification_required": self.verification_required,
            "max_documents": self.max_documents,
            "max_chunks": self.max_chunks,
            "max_iterations": self.max_iterations,
            "budget_cost_limit": self.budget_cost_limit,
            "stop_conditions": [sc.value for sc in self.stop_conditions],
            "parallel_groups": self.parallel_groups,
            "created_at": self.created_at,
        }


@dataclass
class RetrievalStrategyDecision:
    """Strategy decision record providing explainable diagnostic rationale."""
    decision_id: str = field(default_factory=lambda: f"DEC-{uuid.uuid4().hex[:8].upper()}")
    query: str = ""
    complexity: RetrievalComplexity = RetrievalComplexity.SIMPLE
    selected_strategy: RetrievalStrategyType = RetrievalStrategyType.HYBRID
    hybrid_selected: bool = True
    rerank_selected: bool = True
    reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "query": self.query,
            "complexity": self.complexity.value,
            "selected_strategy": self.selected_strategy.value,
            "hybrid_selected": self.hybrid_selected,
            "rerank_selected": self.rerank_selected,
            "reasoning": self.reasoning,
        }
