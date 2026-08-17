"""
SECUROXI AI Phase 2 Stage 5 — Experience & Qualification Analysis Models
Dataclasses for empirical qualification findings, experience breakdowns, and reports.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class QualificationStatus(str, Enum):
    REQUIREMENT_MET = "REQUIREMENT_MET"
    REQUIREMENT_PARTIAL = "REQUIREMENT_PARTIAL"
    REQUIREMENT_NOT_MET = "REQUIREMENT_NOT_MET"
    REQUIREMENT_UNKNOWN = "REQUIREMENT_UNKNOWN"


@dataclass
class QualificationFinding:
    """Represents a single evaluated qualification requirement finding."""
    qualification_name: str
    status: QualificationStatus
    required_level: str
    candidate_evidence: str
    confidence: float
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "qualification_name": self.qualification_name,
            "status": self.status.value,
            "required_level": self.required_level,
            "candidate_evidence": self.candidate_evidence,
            "confidence": round(self.confidence, 2),
            "explanation": self.explanation
        }


@dataclass
class QualificationAnalysisReport:
    """Comprehensive qualification analysis report for candidate resume against JD."""
    resume_id: str
    jd_id: str
    total_relevant_experience_years: float = 0.0
    technology_experience_breakdown: Dict[str, float] = field(default_factory=dict)
    findings: List[QualificationFinding] = field(default_factory=list)
    met_qualifications_count: int = 0
    total_qualifications_count: int = 0
    qualification_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resume_id": self.resume_id,
            "jd_id": self.jd_id,
            "total_relevant_experience_years": round(self.total_relevant_experience_years, 1),
            "technology_experience_breakdown": {
                k: round(v, 1) for k, v in self.technology_experience_breakdown.items()
            },
            "findings": [f.to_dict() for f in self.findings],
            "met_qualifications_count": self.met_qualifications_count,
            "total_qualifications_count": self.total_qualifications_count,
            "qualification_score": round(self.qualification_score, 2)
        }
