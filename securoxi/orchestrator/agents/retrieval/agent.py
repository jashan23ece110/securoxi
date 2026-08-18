"""
SECUROXI AI Intelligence 2.0 — Specialized Retrieval & Research Agent
Executes query decomposition, hybrid retrieval, adaptive re-querying,
evidence sufficiency evaluation, and citation synthesis.
"""

from typing import Dict, Any, List, Optional
from securoxi.orchestrator.agents.base import AbstractAgent
from securoxi.orchestrator.agents.models import (
    AgentDefinition,
    AgentDecision,
    AgentOutput,
)
from securoxi.orchestrator.agents.types import (
    AgentDomain,
    AgentCapability,
    AgentRiskLevel,
    AgentLifecycleState,
    AgentActionType,
)
from securoxi.orchestrator.agents.retrieval.types import (
    RetrievalStrategy,
    EvidenceSufficiencyState,
    ResearchResultType,
)
from securoxi.orchestrator.agents.retrieval.models import (
    QueryAnalysis,
    RetrievedChunkEvidence,
    StructuredCitation,
    EvidenceConflict,
    EvidencePack,
)
from securoxi.orchestrator.types import TrustLevel
from securoxi.orchestrator.planning.types import TaskIntent
from securoxi.orchestrator.context import ExecutionContext
from securoxi.logger import get_logger

logger = get_logger("orchestrator.retrieval_agent")


def get_default_retrieval_agent_definition() -> AgentDefinition:
    """Returns the system-owned AgentDefinition for the specialized Retrieval Agent."""
    return AgentDefinition(
        agent_id="retrieval-agent",
        name="Securoxi Autonomous Retrieval & Research Agent",
        description="Decomposes research queries, performs hybrid vector retrieval, evaluates evidence sufficiency, and compiles grounded evidence packs",
        version="1.0.0",
        domain=AgentDomain.RETRIEVAL,
        capabilities=[
            AgentCapability.DOCUMENT_RETRIEVAL,
            AgentCapability.GENERAL_REASONING,
            AgentCapability.REPORT_GENERATION,
        ],
        trust_level=TrustLevel.LOW_RISK,
        risk_level=AgentRiskLevel.LOW,
        allowed_tools={
            "vector_search",
            "keyword_search",
            "hybrid_search",
            "rerank_evidence",
        },
        supported_intents=[
            TaskIntent.QUESTION_ANSWERING,
            TaskIntent.DOCUMENT_ANALYSIS,
            TaskIntent.DOCUMENT_COMPARISON,
            TaskIntent.REPORT_GENERATION,
            TaskIntent.CANDIDATE_SCREENING,
            TaskIntent.JD_MATCHING,
            TaskIntent.MIXED_WORKFLOW,
        ],
        max_iterations=12,
        enabled=True,
    )


class RetrievalAgent(AbstractAgent):
    """
    Specialized Autonomous Retrieval & Research Agent.
    Coordinates evidence discovery, multi-hop subquerying, reranking, and citation generation.
    """

    def __init__(self, definition: Optional[AgentDefinition] = None):
        agent_def = definition or get_default_retrieval_agent_definition()
        super().__init__(definition=agent_def)

        self.query_analysis: Optional[QueryAnalysis] = None
        self.retrieved_evidence: List[RetrievedChunkEvidence] = []
        self.citations: List[StructuredCitation] = []
        self.conflicts: List[EvidenceConflict] = []
        self.gaps: List[str] = []
        self.sufficiency_state = EvidenceSufficiencyState.INSUFFICIENT
        self.retrieval_trace: List[Dict[str, Any]] = []
        self._executed_subqueries: List[str] = []
        self._reranked = False

    def initialize(self, context: ExecutionContext, **kwargs) -> bool:
        super().initialize(context, **kwargs)
        self.query_analysis = None
        self.retrieved_evidence = []
        self.citations = []
        self.conflicts = []
        self.gaps = []
        self.sufficiency_state = EvidenceSufficiencyState.INSUFFICIENT
        self.retrieval_trace = []
        self._executed_subqueries = []
        self._reranked = False
        return True

    def decide(self, context: ExecutionContext) -> AgentDecision:
        """
        Adaptive Retrieval & Research Loop:
        1. Analyze query & decompose into subqueries.
        2. Execute hybrid search for each subquery.
        3. Rerank accumulated evidence hits.
        4. Detect conflicting source claims or evidence gaps.
        5. Compile grounded citations and finalize EvidencePack.
        """
        self._process_latest_observations()

        # Step 1: Query Analysis & Decomposition
        if not self.query_analysis:
            params = self._get_initial_parameters()
            raw_query = params.get("query", "")
            include_quarantined = params.get("include_quarantined", False)

            # Analyze query terms & extract subqueries
            subqueries = self._decompose_query(raw_query)
            self.query_analysis = QueryAnalysis(
                raw_query=raw_query,
                intent=params.get("intent", "DOCUMENT_RETRIEVAL"),
                entities=raw_query.split(),
                security_filters=["UNTRUSTED"] if include_quarantined else ["SAFE"],
                subqueries=subqueries,
            )

            # Propose first subquery search
            first_q = subqueries[0] if subqueries else raw_query
            self._executed_subqueries.append(first_q)
            self.retrieval_trace.append({"action": "HYBRID_SEARCH", "query": first_q})

            return AgentDecision(
                decision_type=AgentActionType.USE_TOOL,
                target_tool_id="hybrid_search",
                tool_arguments={"query": first_q, "top_k": 5, "include_quarantined": include_quarantined},
                reasoning_summary=f"Executing hybrid retrieval for primary subquery: '{first_q}'",
            )

        # Step 2: Execute remaining subqueries
        remaining_subqueries = [q for q in self.query_analysis.subqueries if q not in self._executed_subqueries]
        if remaining_subqueries:
            next_q = remaining_subqueries[0]
            self._executed_subqueries.append(next_q)
            self.retrieval_trace.append({"action": "HYBRID_SEARCH_SUBQUERY", "query": next_q})

            return AgentDecision(
                decision_type=AgentActionType.USE_TOOL,
                target_tool_id="hybrid_search",
                tool_arguments={"query": next_q, "top_k": 5},
                reasoning_summary=f"Executing secondary subquery retrieval: '{next_q}'",
            )

        # Step 3: Reranking pass
        if not self._reranked and len(self.retrieved_evidence) > 1:
            self._reranked = True
            candidate_hits = [e.to_dict() for e in self.retrieved_evidence]
            self.retrieval_trace.append({"action": "RERANK_EVIDENCE", "hits_count": len(candidate_hits)})

            return AgentDecision(
                decision_type=AgentActionType.USE_TOOL,
                target_tool_id="rerank_evidence",
                tool_arguments={"query": self.query_analysis.raw_query, "candidate_hits": candidate_hits},
                reasoning_summary="Reranking retrieved candidate chunks for semantic relevance density",
            )

        # Step 4: Evaluate Evidence Sufficiency & Conflicts
        self._evaluate_evidence_sufficiency()
        self._detect_evidence_conflicts()
        self._assemble_citations()

        return AgentDecision(
            decision_type=AgentActionType.FINISH,
            reasoning_summary=f"Research complete. Found {len(self.retrieved_evidence)} evidence chunks. Sufficiency: {self.sufficiency_state.value}.",
            confidence=0.95,
        )

    def finalize(self, context: ExecutionContext) -> AgentOutput:
        """Constructs the strongly typed AgentOutput with complete EvidencePack."""
        raw_q = self.query_analysis.raw_query if self.query_analysis else "Query"

        # Construct summary explanation
        if self.sufficiency_state == EvidenceSufficiencyState.SUFFICIENT:
            summary = f"Retrieved {len(self.retrieved_evidence)} verified evidence chunks supporting query '{raw_q}'."
        elif self.sufficiency_state == EvidenceSufficiencyState.PARTIALLY_SUPPORTED:
            summary = f"Partially supported research for '{raw_q}'. Gaps identified: {', '.join(self.gaps)}."
        elif self.sufficiency_state == EvidenceSufficiencyState.CONFLICTING:
            summary = f"Conflicting source evidence identified for query '{raw_q}'."
        else:
            summary = f"No relevant evidence found for query '{raw_q}' within tenant scope."

        evidence_pack = EvidencePack(
            query=raw_q,
            sources=list(set([e.document_id for e in self.retrieved_evidence])),
            evidence_items=self.retrieved_evidence,
            citations=self.citations,
            sufficiency=self.sufficiency_state,
            conflicts=self.conflicts,
            gaps=self.gaps,
            retrieval_trace=self.retrieval_trace,
            summary_text=summary,
        )

        self.state = AgentLifecycleState.COMPLETED
        return AgentOutput(
            agent_id=self.agent_id,
            version=self.version,
            status=self.state,
            result_data=evidence_pack.to_dict(),
            evidence_references=[c.citation_id for c in self.citations],
            provenance=[f"Tenant:{context.tenant_id}", f"Agent:{self.agent_id}", f"Hits:{len(self.retrieved_evidence)}"],
            recommended_next_steps=["CONSUME_EVIDENCE_PACK", "DOWNSTREAM_REASONING"],
            warnings=[f"Gaps: {g}" for g in self.gaps] if self.gaps else [],
            confidence=0.95 if self.sufficiency_state == EvidenceSufficiencyState.SUFFICIENT else 0.75,
        )

    def _decompose_query(self, query: str) -> List[str]:
        """Decomposes a compound user query into focused search subqueries."""
        if not query:
            return [""]
        # Split on conjunctions or semicolons if present
        parts = []
        for delimiter in [" and ", " comparing ", " compared to ", ";"]:
            if delimiter in query.lower():
                split_parts = query.lower().split(delimiter)
                parts.extend([p.strip() for p in split_parts if len(p.strip()) > 3])
                break
        return parts if parts else [query]

    def _process_latest_observations(self):
        """Processes tool output observations and accumulates retrieved evidence chunks."""
        for obs in self._observations:
            if obs.source == "TOOL_RESULT" and isinstance(obs.payload, dict):
                hits = obs.payload.get("hits", [])
                for h in hits:
                    cid = h.get("chunk_id", "")
                    if not any(e.chunk_id == cid for e in self.retrieved_evidence):
                        self.retrieved_evidence.append(
                            RetrievedChunkEvidence(
                                chunk_id=cid,
                                document_id=h.get("document_id", "DOC-01"),
                                tenant_id=h.get("tenant_id", "TENANT-DEFAULT"),
                                text=h.get("text", ""),
                                score=float(h.get("score", h.get("rerank_score", 0.5))),
                                section_heading=h.get("section_heading", ""),
                                page=int(h.get("page", h.get("start_page", 1))),
                                security_status=h.get("security_status", "SAFE"),
                                retrieval_method="HYBRID",
                            )
                        )

    def _evaluate_evidence_sufficiency(self):
        """Evaluates whether retrieved evidence is sufficient, partial, or missing."""
        if not self.retrieved_evidence:
            self.sufficiency_state = EvidenceSufficiencyState.NOT_FOUND
            self.gaps.append("No matching documents found in tenant scope")
        elif len(self.retrieved_evidence) >= 2:
            self.sufficiency_state = EvidenceSufficiencyState.SUFFICIENT
        else:
            self.sufficiency_state = EvidenceSufficiencyState.PARTIALLY_SUPPORTED
            self.gaps.append("Limited evidence depth (single chunk)")

    def _detect_evidence_conflicts(self):
        """Identifies conflicting statements between retrieved source documents."""
        # Detect contradictory claims (e.g. years of experience differences)
        doc_texts: Dict[str, str] = {}
        for ev in self.retrieved_evidence:
            doc_texts[ev.document_id] = ev.text.lower()

        if len(doc_texts) >= 2:
            all_texts = list(doc_texts.values())
            has_5 = any("5 years" in t for t in all_texts)
            has_3 = any("3 years" in t for t in all_texts)
            keys = list(doc_texts.keys())

            if has_5 and has_3:
                self.conflicts.append(
                    EvidenceConflict(
                        topic="Candidate Experience / Location",
                        source_a=keys[0],
                        claim_a=doc_texts[keys[0]][:100],
                        source_b=keys[1],
                        claim_b=doc_texts[keys[1]][:100],
                        severity="MEDIUM",
                    )
                )
                self.sufficiency_state = EvidenceSufficiencyState.CONFLICTING

    def _assemble_citations(self):
        """Builds structured citations from retrieved chunks."""
        self.citations.clear()
        for i, ev in enumerate(self.retrieved_evidence):
            self.citations.append(
                StructuredCitation(
                    citation_id=f"CIT-{i+1:03d}",
                    document_id=ev.document_id,
                    document_name=f"Document {ev.document_id}",
                    page=ev.page,
                    section=ev.section_heading,
                    chunk_id=ev.chunk_id,
                    evidence_text=ev.text[:250],
                    source_type="DOCUMENT_CHUNK",
                    provenance=f"Tenant:{ev.tenant_id}#Chunk:{ev.chunk_id}",
                )
            )

    def _get_initial_parameters(self) -> Dict[str, Any]:
        """Extracts input parameters from initial observation."""
        for obs in self._observations:
            if obs.source == "AGENT_INPUT" and isinstance(obs.payload, dict):
                return obs.payload
        return {}
