"""
SECUROXI AI Intelligence 2.0 — Adaptive Retrieval Execution Data Models
Defines strongly typed models for Evidence Gaps, Retrieval Hops, Execution State,
and the top-level RetrievalExecutionResult contract.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import uuid
import time
from securoxi.orchestrator.retrieval_execution.types import (
    RetrievalHopType,
    EvidenceGapType,
    NextHopDecision,
    RetrievalQualityState,
    StopReason,
)


@dataclass
class EvidenceGap:
    """Individual identified gap in retrieved evidence requiring targeted resolution."""
    gap_id: str = field(default_factory=lambda: f"GAP-{uuid.uuid4().hex[:6].upper()}")
    gap_type: EvidenceGapType = EvidenceGapType.MISSING_CONTEXT
    target_topic: str = ""
    description: str = ""
    required_terms: List[str] = field(default_factory=list)
    suggested_query: str = ""
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "gap_type": self.gap_type.value,
            "target_topic": self.target_topic,
            "description": self.description,
            "required_terms": self.required_terms,
            "suggested_query": self.suggested_query,
            "resolved": self.resolved,
        }


@dataclass
class RetrievalHop:
    """Explicit individual retrieval hop within an adaptive multi-hop execution chain."""
    hop_id: str = field(default_factory=lambda: f"HOP-{uuid.uuid4().hex[:6].upper()}")
    parent_hop_id: Optional[str] = None
    hop_type: RetrievalHopType = RetrievalHopType.ROOT_HOP
    strategy: str = "HYBRID"
    query: str = ""
    source: str = "DOCUMENTS"
    filters: Dict[str, Any] = field(default_factory=dict)
    expected_evidence: str = ""
    chunks_retrieved: List[Dict[str, Any]] = field(default_factory=list)
    evidence_coverage: float = 1.0
    next_decision: NextHopDecision = NextHopDecision.STOP
    status: str = "COMPLETED"
    latency_ms: float = 0.0
    cost: float = 0.0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hop_id": self.hop_id,
            "parent_hop_id": self.parent_hop_id,
            "hop_type": self.hop_type.value,
            "strategy": self.strategy,
            "query": self.query,
            "source": self.source,
            "filters": self.filters,
            "expected_evidence": self.expected_evidence,
            "chunks_retrieved": self.chunks_retrieved,
            "evidence_coverage": round(self.evidence_coverage, 2),
            "next_decision": self.next_decision.value,
            "status": self.status,
            "latency_ms": round(self.latency_ms, 2),
            "cost": self.cost,
            "created_at": self.created_at,
        }


@dataclass
class RetrievalExecutionState:
    """Durable state tracking multi-hop retrieval progress, active gaps, and query history."""
    task_id: str
    run_id: str
    tenant_id: str
    original_objective: str
    completed_hops: List[RetrievalHop] = field(default_factory=list)
    evidence_gaps: List[EvidenceGap] = field(default_factory=list)
    accumulated_evidence: List[Dict[str, Any]] = field(default_factory=list)
    attempted_queries: List[str] = field(default_factory=list)
    searched_sources: List[str] = field(default_factory=list)
    stop_reason: Optional[StopReason] = None
    is_terminated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "run_id": self.run_id,
            "tenant_id": self.tenant_id,
            "original_objective": self.original_objective,
            "completed_hops": [h.to_dict() for h in self.completed_hops],
            "evidence_gaps": [g.to_dict() for g in self.evidence_gaps],
            "accumulated_evidence": self.accumulated_evidence,
            "attempted_queries": self.attempted_queries,
            "searched_sources": self.searched_sources,
            "stop_reason": self.stop_reason.value if self.stop_reason else None,
            "is_terminated": self.is_terminated,
        }


@dataclass
class RetrievalExecutionResult:
    """Comprehensive structured outcome produced by the Adaptive Retrieval Executor."""
    task_id: str
    run_id: str
    tenant_id: str
    query: str
    quality_state: RetrievalQualityState = RetrievalQualityState.SUFFICIENT
    hops: List[RetrievalHop] = field(default_factory=list)
    evidence_pack: Dict[str, Any] = field(default_factory=dict)
    coverage_percentage: float = 100.0
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)
    stop_reason: StopReason = StopReason.EVIDENCE_SUFFICIENT
    iterations: int = 1
    retrieval_trace: List[str] = field(default_factory=list)
    budget_usage: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "run_id": self.run_id,
            "tenant_id": self.tenant_id,
            "query": self.query,
            "quality_state": self.quality_state.value,
            "hops": [h.to_dict() for h in self.hops],
            "evidence_pack": self.evidence_pack,
            "coverage_percentage": round(self.coverage_percentage, 2),
            "conflicts": self.conflicts,
            "citations": self.citations,
            "stop_reason": self.stop_reason.value,
            "iterations": self.iterations,
            "retrieval_trace": self.retrieval_trace,
            "budget_usage": self.budget_usage,
            "warnings": self.warnings,
        }
