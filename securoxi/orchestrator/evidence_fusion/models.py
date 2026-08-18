"""
SECUROXI AI Intelligence 2.0 — Evidence Fusion Data Models
Defines strongly typed models for Retrieval Candidates, Requirement Coverage Items,
Evidence Conflicts, and the top-level FusedEvidenceSet contract.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import uuid
import time
from securoxi.orchestrator.evidence_fusion.types import (
    EvidenceSourceType,
    EvidenceQualityTier,
    CoverageState,
)


@dataclass
class RetrievalCandidate:
    """Individual retrieved evidence chunk with normalized score and source authority."""
    chunk_id: str
    document_id: str
    source: str = "RESUME"
    source_type: EvidenceSourceType = EvidenceSourceType.CANDIDATE_RESUME
    retrieval_method: str = "HYBRID"
    raw_score: float = 1.0
    normalized_score: float = 1.0
    content: str = ""
    security_status: str = "SAFE"
    metadata: Dict[str, Any] = field(default_factory=dict)
    hop_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "source": self.source,
            "source_type": self.source_type.value,
            "retrieval_method": self.retrieval_method,
            "raw_score": round(self.raw_score, 4),
            "normalized_score": round(self.normalized_score, 4),
            "content": self.content,
            "security_status": self.security_status,
            "metadata": self.metadata,
            "hop_id": self.hop_id,
        }


@dataclass
class RequirementCoverageItem:
    """Evaluation of evidence coverage for a specific requirement or topic."""
    requirement_id: str
    topic: str
    state: CoverageState = CoverageState.COMPLETE
    supporting_chunk_ids: List[str] = field(default_factory=list)
    evidence_snippets: List[str] = field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "topic": self.topic,
            "state": self.state.value,
            "supporting_chunk_ids": self.supporting_chunk_ids,
            "evidence_snippets": self.evidence_snippets,
            "confidence": round(self.confidence, 2),
        }


@dataclass
class EvidenceConflict:
    """Preserved contradiction between two distinct sources or claims."""
    conflict_id: str = field(default_factory=lambda: f"CONF-{uuid.uuid4().hex[:6].upper()}")
    topic: str = ""
    claim_a: str = ""
    source_a: str = ""
    claim_b: str = ""
    source_b: str = ""
    authority_resolution: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "topic": self.topic,
            "claim_a": self.claim_a,
            "source_a": self.source_a,
            "claim_b": self.claim_b,
            "source_b": self.source_b,
            "authority_resolution": self.authority_resolution,
        }


@dataclass
class FusedEvidenceSet:
    """Final, consolidated evidence set produced by the Evidence Fusion Engine."""
    fused_id: str = field(default_factory=lambda: f"FUSED-{uuid.uuid4().hex[:8].upper()}")
    task_id: str = "TASK-DEFAULT"
    tenant_id: str = "TENANT-DEFAULT"
    query: str = ""
    ranked_items: List[RetrievalCandidate] = field(default_factory=list)
    requirement_matrix: List[RequirementCoverageItem] = field(default_factory=list)
    conflicts: List[EvidenceConflict] = field(default_factory=list)
    duplicates_removed: int = 0
    overall_coverage: float = 100.0
    quality_tier: EvidenceQualityTier = EvidenceQualityTier.HIGH_CONFIDENCE
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fused_id": self.fused_id,
            "task_id": self.task_id,
            "tenant_id": self.tenant_id,
            "query": self.query,
            "ranked_items": [i.to_dict() for i in self.ranked_items],
            "requirement_matrix": [r.to_dict() for r in self.requirement_matrix],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "duplicates_removed": self.duplicates_removed,
            "overall_coverage": round(self.overall_coverage, 2),
            "quality_tier": self.quality_tier.value,
            "created_at": self.created_at,
        }
