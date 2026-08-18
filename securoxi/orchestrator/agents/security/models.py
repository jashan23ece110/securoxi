"""
SECUROXI AI Intelligence 2.0 — Security Agent Data Models
Defines strongly typed models for Evidence References, Attack Chains, Policy Contexts,
Incident Proposals, and Security Investigation Results.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from securoxi.orchestrator.agents.security.types import (
    SecurityInvestigationState,
    SecurityRecommendationType,
    EvidenceVerificationState,
)


@dataclass
class SecurityEvidenceReference:
    """Traceable evidence item linking findings to exact document locations."""
    evidence_id: str = field(default_factory=lambda: f"EVD-{uuid.uuid4().hex[:8].upper()}")
    finding_id: str = ""
    category: str = "UNKNOWN"
    severity: str = "LOW"
    title: str = ""
    description: str = ""
    original_text_excerpt: str = ""
    page: int = 1
    bbox: Optional[List[float]] = None
    location: str = ""
    analyzer_source: str = "DETERMINISTIC_ENGINE"
    verification_state: EvidenceVerificationState = EvidenceVerificationState.VERIFIED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "finding_id": self.finding_id,
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "original_text_excerpt": self.original_text_excerpt,
            "page": self.page,
            "bbox": self.bbox,
            "location": self.location,
            "analyzer_source": self.analyzer_source,
            "verification_state": self.verification_state.value,
        }


@dataclass
class SecurityAttackStep:
    """An individual step or tactic in a synthesized attack chain."""
    step_index: int = 1
    category: str = ""
    description: str = ""
    relationship_type: str = "OBSERVED"  # "OBSERVED", "CORRELATED", "INFERRED"
    evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "category": self.category,
            "description": self.description,
            "relationship_type": self.relationship_type,
            "evidence_ids": self.evidence_ids,
        }


@dataclass
class SecurityAttackChainSummary:
    """Correlated attack chain connecting multiple deception or injection findings."""
    chain_id: str = field(default_factory=lambda: f"CHAIN-{uuid.uuid4().hex[:8].upper()}")
    title: str = ""
    severity: str = "HIGH"
    steps: List[SecurityAttackStep] = field(default_factory=list)
    impact_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "title": self.title,
            "severity": self.severity,
            "steps": [s.to_dict() for s in self.steps],
            "impact_summary": self.impact_summary,
        }


@dataclass
class SecurityPolicyContext:
    """Authoritative policy evaluation summary for the investigated asset."""
    policy_id: str = "DEFAULT-POLICY"
    rule_name: str = "Standard Security Gate"
    action: str = "ALLOW"  # "ALLOW", "REVIEW", "QUARANTINE", "BLOCK"
    priority: int = 10
    authoritative_verdict: str = "SAFE"
    explanation: str = "No policy restrictions triggered"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "rule_name": self.rule_name,
            "action": self.action,
            "priority": self.priority,
            "authoritative_verdict": self.authoritative_verdict,
            "explanation": self.explanation,
        }


@dataclass
class SecurityRiskContext:
    """Authoritative risk scoring context sourced from Risk Engine."""
    risk_score: float = 0.0
    risk_tier: str = "LOW"  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    explanation: str = "Low risk detected"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_score": self.risk_score,
            "risk_tier": self.risk_tier,
            "explanation": self.explanation,
        }


@dataclass
class IncidentProposal:
    """Structured incident proposal drafted when high-risk threats are identified."""
    incident_id: str = field(default_factory=lambda: f"INC-PROP-{uuid.uuid4().hex[:8].upper()}")
    title: str = ""
    severity: str = "HIGH"
    summary: str = ""
    affected_document_ids: List[str] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    requires_human_approval: bool = True
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "title": self.title,
            "severity": self.severity,
            "summary": self.summary,
            "affected_document_ids": self.affected_document_ids,
            "findings": self.findings,
            "recommended_actions": self.recommended_actions,
            "requires_human_approval": self.requires_human_approval,
            "created_at": self.created_at,
        }


@dataclass
class SecurityAgentResult:
    """Comprehensive, validated output delivered by the Security Agent."""
    document_id: str = ""
    authoritative_security_state: str = "SAFE"  # Sourced from deterministic scanner
    findings_count: int = 0
    evidence_items: List[SecurityEvidenceReference] = field(default_factory=list)
    attack_chains: List[SecurityAttackChainSummary] = field(default_factory=list)
    policy_context: Optional[SecurityPolicyContext] = None
    risk_context: Optional[SecurityRiskContext] = None
    incident_proposal: Optional[IncidentProposal] = None
    recommended_actions: List[SecurityRecommendationType] = field(default_factory=lambda: [SecurityRecommendationType.NO_ACTION])
    user_explanation: str = "Security scan complete. No security findings detected."
    provenance_chain: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    verification_state: EvidenceVerificationState = EvidenceVerificationState.VERIFIED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "authoritative_security_state": self.authoritative_security_state,
            "findings_count": self.findings_count,
            "evidence_items": [e.to_dict() for e in self.evidence_items],
            "attack_chains": [c.to_dict() for c in self.attack_chains],
            "policy_context": self.policy_context.to_dict() if self.policy_context else None,
            "risk_context": self.risk_context.to_dict() if self.risk_context else None,
            "incident_proposal": self.incident_proposal.to_dict() if self.incident_proposal else None,
            "recommended_actions": [r.value for r in self.recommended_actions],
            "user_explanation": self.user_explanation,
            "provenance_chain": self.provenance_chain,
            "warnings": self.warnings,
            "verification_state": self.verification_state.value,
        }
