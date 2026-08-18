"""
SECUROXI AI Intelligence 2.0 — Hiring & Screening Agent Data Models
Defines strongly typed models for JD Analysis, Candidate Screening Results,
and the top-level HiringAgentResult contract.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from securoxi.orchestrator.agents.hiring.types import (
    CandidateQualificationState,
    RequirementType,
    EvidenceQualityTier,
    ATSOperationType,
)


@dataclass
class RequirementCriterion:
    """Individual screening criterion extracted from a Job Description."""
    req_id: str
    name: str
    req_type: RequirementType = RequirementType.MANDATORY
    description: str = ""
    min_years: float = 0.0
    required_skills: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "req_id": self.req_id,
            "name": self.name,
            "req_type": self.req_type.value,
            "description": self.description,
            "min_years": self.min_years,
            "required_skills": self.required_skills,
        }


@dataclass
class JDAnalysis:
    """Structured decomposition and requirements extracted from a Job Description."""
    job_id: str = "JD-DEFAULT"
    title: str = "Software Engineer"
    mandatory_requirements: List[RequirementCriterion] = field(default_factory=list)
    preferred_requirements: List[RequirementCriterion] = field(default_factory=list)
    exclusions: List[str] = field(default_factory=lambda: ["HIGH_RISK", "UNINSPECTABLE"])
    raw_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "title": self.title,
            "mandatory_requirements": [m.to_dict() for m in self.mandatory_requirements],
            "preferred_requirements": [p.to_dict() for p in self.preferred_requirements],
            "exclusions": self.exclusions,
            "raw_text": self.raw_text,
        }


@dataclass
class CandidateScreeningResult:
    """Evaluation result for an individual candidate within the hiring pipeline."""
    candidate_id: str
    candidate_name: str
    security_status: str = "SAFE"
    qualification_state: CandidateQualificationState = CandidateQualificationState.QUALIFIED
    fit_score: float = 0.0
    matched_mandatory: List[str] = field(default_factory=list)
    matched_preferred: List[str] = field(default_factory=list)
    missing_requirements: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    rank: int = 1
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "security_status": self.security_status,
            "qualification_state": self.qualification_state.value,
            "fit_score": round(self.fit_score, 2),
            "matched_mandatory": self.matched_mandatory,
            "matched_preferred": self.matched_preferred,
            "missing_requirements": self.missing_requirements,
            "evidence": self.evidence,
            "citations": self.citations,
            "conflicts": self.conflicts,
            "warnings": self.warnings,
            "rank": self.rank,
            "explanation": self.explanation,
        }


@dataclass
class HiringAgentResult:
    """Comprehensive structured hiring evaluation output produced by the Hiring Agent."""
    task_summary: str = ""
    job_context: Dict[str, Any] = field(default_factory=dict)
    security_summary: Dict[str, Any] = field(default_factory=dict)
    candidate_results: List[CandidateScreeningResult] = field(default_factory=list)
    qualified_candidates: List[str] = field(default_factory=list)
    near_matches: List[str] = field(default_factory=list)
    quarantined_candidates: List[str] = field(default_factory=list)
    shortlist: List[str] = field(default_factory=list)
    approval_requirements: List[Dict[str, Any]] = field(default_factory=list)
    total_discovered: int = 0
    total_evaluated: int = 0
    is_partial_coverage: bool = False
    coverage_percentage: float = 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_summary": self.task_summary,
            "job_context": self.job_context,
            "security_summary": self.security_summary,
            "candidate_results": [c.to_dict() for c in self.candidate_results],
            "qualified_candidates": self.qualified_candidates,
            "near_matches": self.near_matches,
            "quarantined_candidates": self.quarantined_candidates,
            "shortlist": self.shortlist,
            "approval_requirements": self.approval_requirements,
            "total_discovered": self.total_discovered,
            "total_evaluated": self.total_evaluated,
            "is_partial_coverage": self.is_partial_coverage,
            "coverage_percentage": round(self.coverage_percentage, 2),
        }
