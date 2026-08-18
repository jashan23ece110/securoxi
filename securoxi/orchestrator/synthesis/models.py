"""
SECUROXI AI Intelligence 2.0 — Cross-Document Research Synthesis Data Models
Defines strongly typed models for Derived Claims, Comparison Items, and the top-level
SynthesisResult contract.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import uuid
import time
from securoxi.orchestrator.synthesis.types import (
    SynthesisMode,
    ComparisonDimension,
    SynthesisStatus,
)


@dataclass
class DerivedClaim:
    """Higher-order conclusion derived by synthesizing multiple underlying verified claims."""
    derived_claim_id: str = field(default_factory=lambda: f"DCLM-{uuid.uuid4().hex[:6].upper()}")
    text: str = ""
    source_claim_ids: List[str] = field(default_factory=list)
    derivation_rationale: str = ""
    is_reverified: bool = True
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "derived_claim_id": self.derived_claim_id,
            "text": self.text,
            "source_claim_ids": self.source_claim_ids,
            "derivation_rationale": self.derivation_rationale,
            "is_reverified": self.is_reverified,
            "confidence": round(self.confidence, 2),
        }


@dataclass
class ComparisonItem:
    """Structured dimension-by-dimension comparison between multiple entities."""
    dimension: str
    entity_a_value: str
    entity_b_value: str
    comparison_verdict: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "entity_a_value": self.entity_a_value,
            "entity_b_value": self.entity_b_value,
            "comparison_verdict": self.comparison_verdict,
        }


@dataclass
class SynthesisResult:
    """Final grounded research synthesis across multiple documents and verified claims."""
    result_id: str = field(default_factory=lambda: f"SYNTH-{uuid.uuid4().hex[:8].upper()}")
    task_id: str = "TASK-DEFAULT"
    tenant_id: str = "TENANT-DEFAULT"
    mode: SynthesisMode = SynthesisMode.DIRECT_ANSWER
    executive_summary: str = ""
    detailed_answer: str = ""
    derived_claims: List[DerivedClaim] = field(default_factory=list)
    comparisons: List[ComparisonItem] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    unresolved_conflicts: List[Dict[str, Any]] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)
    groundedness_state: str = "FULLY_GROUNDED"
    status: SynthesisStatus = SynthesisStatus.COMPLETED
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "task_id": self.task_id,
            "tenant_id": self.tenant_id,
            "mode": self.mode.value,
            "executive_summary": self.executive_summary,
            "detailed_answer": self.detailed_answer,
            "derived_claims": [d.to_dict() for d in self.derived_claims],
            "comparisons": [c.to_dict() for c in self.comparisons],
            "recommendations": self.recommendations,
            "unresolved_conflicts": self.unresolved_conflicts,
            "citations": self.citations,
            "groundedness_state": self.groundedness_state,
            "status": self.status.value,
            "created_at": self.created_at,
        }
