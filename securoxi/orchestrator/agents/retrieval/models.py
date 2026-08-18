"""
SECUROXI AI Intelligence 2.0 — Retrieval & Research Agent Data Models
Defines strongly typed models for Query Analysis, Retrieved Evidence Chunks,
Structured Citations, Evidence Conflicts, and Evidence Packs.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from securoxi.orchestrator.agents.retrieval.types import (
    RetrievalStrategy,
    EvidenceSufficiencyState,
    ResearchResultType,
)


@dataclass
class QueryAnalysis:
    """Structured decomposition and intent breakdown of an input research query."""
    raw_query: str = ""
    intent: str = "DOCUMENT_RETRIEVAL"
    entities: List[str] = field(default_factory=list)
    security_filters: List[str] = field(default_factory=lambda: ["SAFE"])
    subqueries: List[str] = field(default_factory=list)
    target_sources: List[str] = field(default_factory=lambda: ["DOCUMENTS"])
    required_evidence_types: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_query": self.raw_query,
            "intent": self.intent,
            "entities": self.entities,
            "security_filters": self.security_filters,
            "subqueries": self.subqueries,
            "target_sources": self.target_sources,
            "required_evidence_types": self.required_evidence_types,
        }


@dataclass
class RetrievedChunkEvidence:
    """Individual retrieved text chunk enriched with relevance score and provenance."""
    chunk_id: str = ""
    document_id: str = ""
    tenant_id: str = "TENANT-DEFAULT"
    text: str = ""
    score: float = 0.0
    section_heading: str = ""
    page: int = 1
    security_status: str = "SAFE"
    retrieval_method: str = "HYBRID"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "tenant_id": self.tenant_id,
            "text": self.text,
            "score": round(self.score, 4),
            "section_heading": self.section_heading,
            "page": self.page,
            "security_status": self.security_status,
            "retrieval_method": self.retrieval_method,
            "timestamp": self.timestamp,
        }


@dataclass
class StructuredCitation:
    """Verifiable citation linking evidence directly to an immutable source document."""
    citation_id: str = field(default_factory=lambda: f"CIT-{uuid.uuid4().hex[:8].upper()}")
    document_id: str = ""
    document_name: str = ""
    page: int = 1
    section: str = ""
    chunk_id: str = ""
    evidence_text: str = ""
    source_type: str = "DOCUMENT"
    provenance: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "citation_id": self.citation_id,
            "document_id": self.document_id,
            "document_name": self.document_name,
            "page": self.page,
            "section": self.section,
            "chunk_id": self.chunk_id,
            "evidence_text": self.evidence_text,
            "source_type": self.source_type,
            "provenance": self.provenance,
        }


@dataclass
class EvidenceConflict:
    """Contradiction or factual discrepancy identified between multiple sources."""
    conflict_id: str = field(default_factory=lambda: f"CONF-{uuid.uuid4().hex[:8].upper()}")
    topic: str = ""
    source_a: str = ""
    claim_a: str = ""
    source_b: str = ""
    claim_b: str = ""
    severity: str = "MEDIUM"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "topic": self.topic,
            "source_a": self.source_a,
            "claim_a": self.claim_a,
            "source_b": self.source_b,
            "claim_b": self.claim_b,
            "severity": self.severity,
        }


@dataclass
class EvidencePack:
    """Comprehensive grounded evidence package assembled by the Retrieval Agent."""
    query: str = ""
    sources: List[str] = field(default_factory=list)
    evidence_items: List[RetrievedChunkEvidence] = field(default_factory=list)
    citations: List[StructuredCitation] = field(default_factory=list)
    sufficiency: EvidenceSufficiencyState = EvidenceSufficiencyState.SUFFICIENT
    conflicts: List[EvidenceConflict] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    retrieval_trace: List[Dict[str, Any]] = field(default_factory=list)
    summary_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "sources": self.sources,
            "evidence_items": [e.to_dict() for e in self.evidence_items],
            "citations": [c.to_dict() for c in self.citations],
            "sufficiency": self.sufficiency.value,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "gaps": self.gaps,
            "retrieval_trace": self.retrieval_trace,
            "summary_text": self.summary_text,
        }
