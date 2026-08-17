"""
SECUROXI AI Phase 2 Stage 6 — Candidate Scoring & Ranking Models
Dataclasses for configurable scoring weights, score reports, strengths, gaps, and candidate rankings.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ScoringWeights:
    """Configurable scoring weights for Candidate Fit Score calculation."""
    required_skills_weight: float = 0.50
    experience_weight: float = 0.25
    preferred_skills_weight: float = 0.15
    education_cert_weight: float = 0.10
    mandatory_missing_penalty_ceiling: float = 50.0  # Max score if required skills are missing

    def to_dict(self) -> Dict[str, Any]:
        return {
            "required_skills_weight": self.required_skills_weight,
            "experience_weight": self.experience_weight,
            "preferred_skills_weight": self.preferred_skills_weight,
            "education_cert_weight": self.education_cert_weight,
            "mandatory_missing_penalty_ceiling": self.mandatory_missing_penalty_ceiling
        }


@dataclass
class CandidateScoreReport:
    """Explainable candidate fit score report with requirement breakdown, strengths, and gaps."""
    candidate_id: str
    candidate_name: str
    jd_id: str
    fit_score: float  # 0.0 to 100.0
    fit_category: str  # EXCELLENT_FIT, STRONG_FIT, PARTIAL_FIT, WEAK_FIT
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    strengths: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    security_verdict: str = "SAFE"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "jd_id": self.jd_id,
            "fit_score": round(self.fit_score, 1),
            "fit_category": self.fit_category,
            "score_breakdown": {k: round(v, 1) for k, v in self.score_breakdown.items()},
            "strengths": self.strengths,
            "gaps": self.gaps,
            "uncertainties": self.uncertainties,
            "security_verdict": self.security_verdict
        }


@dataclass
class RankedCandidatesReport:
    """Report ranking multiple candidate resume profiles against a single JD."""
    jd_id: str
    job_title: str
    total_candidates: int
    ranked_candidates: List[CandidateScoreReport] = field(default_factory=list)
    weights_used: ScoringWeights = field(default_factory=ScoringWeights)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "jd_id": self.jd_id,
            "job_title": self.job_title,
            "total_candidates": self.total_candidates,
            "ranked_candidates": [c.to_dict() for c in self.ranked_candidates],
            "weights_used": self.weights_used.to_dict()
        }
