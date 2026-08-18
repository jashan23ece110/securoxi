"""
SECUROXI AI Intelligence 2.0 — Forensic Agent Data Models
Defines strongly typed models for Forensic Locations, Findings, Attack Steps,
Attack Chains, and the top-level ForensicInvestigationResult contract.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import uuid
from securoxi.orchestrator.agents.forensic.types import (
    ForensicFindingStatus,
    EvidenceSufficiencyTier,
)


@dataclass
class ForensicLocation:
    """Precise spatial and document layout provenance for a forensic finding."""
    page: int = 1
    bbox: Optional[List[float]] = None
    section: str = "Body"
    source_type: str = "PDF_TEXT_SPAN"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page": self.page,
            "bbox": self.bbox,
            "section": self.section,
            "source_type": self.source_type,
        }


@dataclass
class ForensicFinding:
    """Individual investigated finding with verified forensic evidence."""
    finding_id: str
    document_id: str
    category: str
    severity: str
    title: str
    evidence_text: str
    location: ForensicLocation = field(default_factory=ForensicLocation)
    status: ForensicFindingStatus = ForensicFindingStatus.OBSERVED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "document_id": self.document_id,
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "evidence_text": self.evidence_text,
            "location": self.location.to_dict(),
            "status": self.status.value,
        }


@dataclass
class ForensicAttackStep:
    """Individual verified step in an attack graph."""
    step_index: int
    phase: str
    technique: str
    evidence_ref: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "phase": self.phase,
            "technique": self.technique,
            "evidence_ref": self.evidence_ref,
            "description": self.description,
        }


@dataclass
class ForensicAttackChain:
    """Correlated multi-stage attack representation."""
    chain_id: str = field(default_factory=lambda: f"CHAIN-{uuid.uuid4().hex[:8].upper()}")
    steps: List[ForensicAttackStep] = field(default_factory=list)
    confidence: str = "SUPPORTED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "steps": [s.to_dict() for s in self.steps],
            "confidence": self.confidence,
        }


@dataclass
class ForensicInvestigationResult:
    """Comprehensive structured output produced by the Forensic Agent."""
    investigation_id: str = field(default_factory=lambda: f"INV-{uuid.uuid4().hex[:8].upper()}")
    subject: str = ""
    security_state: str = "SAFE"
    findings: List[ForensicFinding] = field(default_factory=list)
    attack_chain: Optional[ForensicAttackChain] = None
    sufficiency: EvidenceSufficiencyTier = EvidenceSufficiencyTier.SUFFICIENT
    recommendations: List[str] = field(default_factory=list)
    provenance: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "subject": self.subject,
            "security_state": self.security_state,
            "findings": [f.to_dict() for f in self.findings],
            "attack_chain": self.attack_chain.to_dict() if self.attack_chain else None,
            "sufficiency": self.sufficiency.value,
            "recommendations": self.recommendations,
            "provenance": self.provenance,
        }
