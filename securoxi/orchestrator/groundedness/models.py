"""
SECUROXI AI Intelligence 2.0 — Groundedness Verification Data Models
Defines strongly typed models for Atomic Claims, Citations, and the top-level
VerifiedEvidencePackage contract.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import uuid
import time
from securoxi.orchestrator.groundedness.types import (
    ClaimType,
    EvidenceSupportState,
    GroundednessState,
    AnswerStatus,
)


@dataclass
class Claim:
    """Atomic factual assertion extracted from reasoning output requiring verification."""
    claim_id: str = field(default_factory=lambda: f"CLM-{uuid.uuid4().hex[:6].upper()}")
    text: str = ""
    claim_type: ClaimType = ClaimType.FACTUAL
    subject: str = ""
    predicate: str = ""
    object_value: str = ""
    supporting_chunk_ids: List[str] = field(default_factory=list)
    support_state: EvidenceSupportState = EvidenceSupportState.UNSUPPORTED
    repaired_text: Optional[str] = None
    citation_ids: List[str] = field(default_factory=list)
    is_verified: bool = False
    untrusted_instruction_detected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "claim_type": self.claim_type.value,
            "subject": self.subject,
            "predicate": self.predicate,
            "object_value": self.object_value,
            "supporting_chunk_ids": self.supporting_chunk_ids,
            "support_state": self.support_state.value,
            "repaired_text": self.repaired_text,
            "citation_ids": self.citation_ids,
            "is_verified": self.is_verified,
            "untrusted_instruction_detected": self.untrusted_instruction_detected,
        }


@dataclass
class Citation:
    """Validated citation referencing an authoritative source document chunk."""
    citation_id: str = field(default_factory=lambda: f"CIT-{uuid.uuid4().hex[:6].upper()}")
    document_id: str = ""
    chunk_id: str = ""
    source: str = "RESUME"
    page: Optional[int] = 1
    snippet: str = ""
    tenant_id: str = "TENANT-DEFAULT"
    is_valid: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "citation_id": self.citation_id,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "source": self.source,
            "page": self.page,
            "snippet": self.snippet,
            "tenant_id": self.tenant_id,
            "is_valid": self.is_valid,
        }


@dataclass
class VerifiedEvidencePackage:
    """Final, grounded evidence and claim package produced by the Groundedness Verifier."""
    package_id: str = field(default_factory=lambda: f"VEP-{uuid.uuid4().hex[:8].upper()}")
    task_id: str = "TASK-DEFAULT"
    tenant_id: str = "TENANT-DEFAULT"
    query: str = ""
    groundedness_state: GroundednessState = GroundednessState.FULLY_GROUNDED
    answer_status: AnswerStatus = AnswerStatus.GROUNDED
    claims: List[Claim] = field(default_factory=list)
    verified_claims: List[Claim] = field(default_factory=list)
    qualified_claims: List[Claim] = field(default_factory=list)
    rejected_claims: List[Claim] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    claim_coverage_pct: float = 100.0
    citation_precision_pct: float = 100.0
    security_state: str = "SAFE"
    verification_trace: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "package_id": self.package_id,
            "task_id": self.task_id,
            "tenant_id": self.tenant_id,
            "query": self.query,
            "groundedness_state": self.groundedness_state.value,
            "answer_status": self.answer_status.value,
            "claims": [c.to_dict() for c in self.claims],
            "verified_claims": [c.to_dict() for c in self.verified_claims],
            "qualified_claims": [c.to_dict() for c in self.qualified_claims],
            "rejected_claims": [c.to_dict() for c in self.rejected_claims],
            "citations": [cit.to_dict() for cit in self.citations],
            "conflicts": self.conflicts,
            "claim_coverage_pct": round(self.claim_coverage_pct, 2),
            "citation_precision_pct": round(self.citation_precision_pct, 2),
            "security_state": self.security_state,
            "verification_trace": self.verification_trace,
            "created_at": self.created_at,
        }
