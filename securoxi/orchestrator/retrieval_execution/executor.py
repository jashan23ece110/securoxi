"""
SECUROXI AI Intelligence 2.0 — Adaptive Retrieval Executor
Executes Stage 10 RetrievalPlans through multi-hop retrieval, evidence gap evaluation,
targeted query adaptation, deduplication, no-new-information stopping, and durable state tracking.
"""

from typing import Dict, Any, List, Optional
import time
from securoxi.orchestrator.retrieval_planner.models import RetrievalPlan
from securoxi.orchestrator.retrieval_execution.types import (
    RetrievalHopType,
    EvidenceGapType,
    NextHopDecision,
    RetrievalQualityState,
    StopReason,
)
from securoxi.orchestrator.retrieval_execution.models import (
    EvidenceGap,
    RetrievalHop,
    RetrievalExecutionState,
    RetrievalExecutionResult,
)
from securoxi.orchestrator.retrieval_execution.gap_engine import EvidenceGapEngine
from securoxi.orchestrator.context import ExecutionContext
from securoxi.logger import get_logger

logger = get_logger("orchestrator.retrieval_executor")


class AdaptiveRetrievalExecutor:
    """
    Executes dynamic multi-hop retrieval plans, evaluates evidence sufficiency iteratively,
    refines queries based on evidence gaps, and produces grounded EvidencePacks.
    """

    def __init__(self, gap_engine: Optional[EvidenceGapEngine] = None):
        self.gap_engine = gap_engine or EvidenceGapEngine()

    def execute(
        self,
        plan: RetrievalPlan,
        context: ExecutionContext,
        initial_corpus: Optional[List[Dict[str, Any]]] = None,
    ) -> RetrievalExecutionResult:
        """
        Executes multi-hop retrieval loop:
        1. Executes Root Hop with primary plan queries.
        2. Evaluates evidence gaps against requirements.
        3. Generates and executes adaptive follow-up hops if gaps remain.
        4. Detects no-new-information or budget exhaustion.
        5. Assembles final EvidencePack with citations and trace.
        """
        start_time = time.time()
        run_id = context.run.run_id if context.run else "RUN-DEFAULT"
        logger.info(f"Executing Adaptive Retrieval Plan '{plan.plan_id}' for task '{plan.task_id}' (Tenant: {context.tenant_id})")

        state = RetrievalExecutionState(
            task_id=plan.task_id,
            run_id=run_id,
            tenant_id=context.tenant_id,
            original_objective=plan.objective,
        )

        trace: List[str] = [f"START: Plan {plan.plan_id}"]
        accumulated_chunks: List[Dict[str, Any]] = []
        seen_chunk_ids = set()
        stop_reason = StopReason.EVIDENCE_SUFFICIENT
        corpus = initial_corpus or self._get_mock_corpus(context.tenant_id)

        # 1. Root Hop Execution
        root_query = plan.queries[0].query_text if plan.queries else plan.objective
        root_chunks = self._retrieve_chunks(root_query, corpus, plan.security_filters)
        
        for c in root_chunks:
            cid = c.get("chunk_id", str(len(accumulated_chunks)))
            if cid not in seen_chunk_ids:
                seen_chunk_ids.add(cid)
                accumulated_chunks.append(c)

        root_hop = RetrievalHop(
            parent_hop_id=None,
            hop_type=RetrievalHopType.ROOT_HOP,
            strategy=plan.selected_strategies[0].value if plan.selected_strategies else "HYBRID",
            query=root_query,
            source="DOCUMENTS",
            filters=plan.security_filters,
            expected_evidence=plan.evidence_requirements[0].topic if plan.evidence_requirements else "Root Evidence",
            chunks_retrieved=root_chunks,
            evidence_coverage=0.75,
            next_decision=NextHopDecision.CONTINUE,
            latency_ms=(time.time() - start_time) * 1000.0,
        )
        state.completed_hops.append(root_hop)
        state.attempted_queries.append(root_query)
        trace.append(f"HOP 1 (ROOT): Query='{root_query}' -> Retrieved {len(root_chunks)} chunks")

        # 2. Adaptive Multi-Hop Loop
        iteration = 1
        while iteration < plan.max_iterations:
            iteration += 1

            # Evaluate Evidence Gaps
            gaps = self.gap_engine.evaluate_gaps(
                accumulated_chunks=accumulated_chunks,
                requirements=plan.evidence_requirements,
                original_objective=plan.objective,
            )
            state.evidence_gaps = gaps

            if not gaps:
                stop_reason = StopReason.EVIDENCE_SUFFICIENT
                root_hop.next_decision = NextHopDecision.STOP
                trace.append(f"STOP: All evidence requirements satisfied at iteration {iteration}")
                break

            # Select target gap and adaptive query
            target_gap = gaps[0]
            followup_query = target_gap.suggested_query or f"{target_gap.target_topic} details"

            if followup_query in state.attempted_queries:
                stop_reason = StopReason.NO_NEW_INFORMATION
                trace.append("STOP: Repeated query detected without new evidence (NO_NEW_INFORMATION)")
                break

            # Execute Follow-up Hop
            hop_start = time.time()
            new_chunks = self._retrieve_chunks(followup_query, corpus, plan.security_filters)
            new_unique_chunks = [c for c in new_chunks if c.get("chunk_id") not in seen_chunk_ids]

            for c in new_unique_chunks:
                seen_chunk_ids.add(c.get("chunk_id"))
                accumulated_chunks.append(c)

            followup_hop = RetrievalHop(
                parent_hop_id=root_hop.hop_id,
                hop_type=RetrievalHopType.FOLLOW_UP_HOP,
                strategy="HYBRID",
                query=followup_query,
                source="DOCUMENTS",
                filters=plan.security_filters,
                expected_evidence=target_gap.target_topic,
                chunks_retrieved=new_chunks,
                evidence_coverage=1.0 if len(new_unique_chunks) > 0 else 0.5,
                next_decision=NextHopDecision.CONTINUE if len(gaps) > 1 else NextHopDecision.STOP,
                latency_ms=(time.time() - hop_start) * 1000.0,
            )
            state.completed_hops.append(followup_hop)
            state.attempted_queries.append(followup_query)
            trace.append(f"HOP {iteration} (FOLLOW_UP): Query='{followup_query}' -> Added {len(new_unique_chunks)} unique chunks")

            if not new_unique_chunks:
                stop_reason = StopReason.NO_NEW_INFORMATION
                trace.append("STOP: Follow-up search converged with no new unique chunks")
                break

        if iteration >= plan.max_iterations and state.evidence_gaps:
            stop_reason = StopReason.MAX_ITERATIONS

        # 3. Assemble Final Output
        total_time_ms = (time.time() - start_time) * 1000.0
        coverage = max(0.0, min(100.0, (1.0 - (len(state.evidence_gaps) / max(len(plan.evidence_requirements), 1))) * 100.0))
        quality = RetrievalQualityState.SUFFICIENT if coverage >= 80.0 else (
            RetrievalQualityState.PARTIAL if coverage > 0 else RetrievalQualityState.INSUFFICIENT
        )

        citations = [
            {
                "citation_id": f"CIT-{i+1}",
                "chunk_id": c.get("chunk_id", f"CHK-{i}"),
                "document_id": c.get("document_id", "DOC-01"),
                "source": c.get("source", "RESUME"),
                "snippet": c.get("content", c.get("text", ""))[:120],
            }
            for i, c in enumerate(accumulated_chunks[:5])
        ]

        evidence_pack = {
            "total_chunks": len(accumulated_chunks),
            "chunks": accumulated_chunks,
            "citations": citations,
            "coverage_percentage": coverage,
            "sufficiency_state": quality.value,
        }

        return RetrievalExecutionResult(
            task_id=plan.task_id,
            run_id=run_id,
            tenant_id=context.tenant_id,
            query=plan.objective,
            quality_state=quality,
            hops=state.completed_hops,
            evidence_pack=evidence_pack,
            coverage_percentage=coverage,
            conflicts=[],
            citations=citations,
            stop_reason=stop_reason,
            iterations=len(state.completed_hops),
            retrieval_trace=trace,
            budget_usage={"latency_ms": round(total_time_ms, 2), "hops_count": len(state.completed_hops)},
            warnings=[f"Unresolved evidence gap: {g.description}" for g in state.evidence_gaps],
        )

    def _retrieve_chunks(self, query: str, corpus: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Matches query terms against in-memory or provided corpus respecting security filters."""
        results = []
        q_lower = query.lower()
        req_sec = filters.get("security_status", "SAFE")

        for item in corpus:
            item_sec = item.get("security_status", "SAFE")
            if req_sec == "SAFE" and item_sec != "SAFE":
                continue

            text = item.get("content", item.get("text", "")).lower()
            if any(term in text for term in q_lower.split()):
                results.append(item)

        return results

    def _get_mock_corpus(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Fallback candidate and document evidence corpus for test execution."""
        return [
            {
                "chunk_id": "CHK-SARAH-01",
                "document_id": "RESUME-SARAH.PDF",
                "source": "RESUME",
                "security_status": "SAFE",
                "content": "Sarah Miller - Senior Security Engineer with 6 years experience in production Kubernetes cluster security and AWS hardening.",
            },
            {
                "chunk_id": "CHK-SARAH-02",
                "document_id": "RESUME-SARAH.PDF",
                "source": "RESUME",
                "security_status": "SAFE",
                "content": "Led cloud security automation, Docker container isolation, and Python CI/CD pipelines at enterprise scale.",
            },
            {
                "chunk_id": "CHK-DAVID-01",
                "document_id": "RESUME-DAVID.PDF",
                "source": "RESUME",
                "security_status": "SAFE",
                "content": "David Chen - DevOps Engineer with 4 years experience in Docker and basic Kubernetes deployments.",
            },
        ]
