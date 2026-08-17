"""
SECUROXI AI Phase 2 Stage 4 — Semantic Matching Models
Dataclasses for requirement-level matches, match statuses, and matching reports.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class MatchStatus(str, Enum):
    MATCH = "MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    NO_MATCH = "NO_MATCH"
    UNKNOWN = "UNKNOWN"


class MatchType(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    NORMALIZED_MATCH = "NORMALIZED_MATCH"
    SEMANTIC_RELATED = "SEMANTIC_RELATED"
    EXPERIENCE_MATCH = "EXPERIENCE_MATCH"
    EDUCATION_MATCH = "EDUCATION_MATCH"
    NO_MATCH = "NO_MATCH"


@dataclass
class RequirementMatch:
    """Represents a single job requirement match evaluation against candidate evidence."""
    requirement: str
    is_required: bool  # True for required, False for preferred
    candidate_evidence: str
    match_status: MatchStatus
    match_type: MatchType
    confidence: float
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirement": self.requirement,
            "is_required": self.is_required,
            "candidate_evidence": self.candidate_evidence,
            "match_status": self.match_status.value,
            "match_type": self.match_type.value,
            "confidence": round(self.confidence, 2),
            "explanation": self.explanation
        }


@dataclass
class MatchingReport:
    """Comprehensive requirement-level matching report between candidate resume and JD."""
    resume_id: str
    jd_id: str
    required_skill_matches: List[RequirementMatch] = field(default_factory=list)
    preferred_skill_matches: List[RequirementMatch] = field(default_factory=list)
    experience_match: Optional[RequirementMatch] = None
    education_match: Optional[RequirementMatch] = None
    total_required_count: int = 0
    matched_required_count: int = 0
    overall_match_ratio: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resume_id": self.resume_id,
            "jd_id": self.jd_id,
            "required_skill_matches": [r.to_dict() for r in self.required_skill_matches],
            "preferred_skill_matches": [p.to_dict() for p in self.preferred_skill_matches],
            "experience_match": self.experience_match.to_dict() if self.experience_match else None,
            "education_match": self.education_match.to_dict() if self.education_match else None,
            "total_required_count": self.total_required_count,
            "matched_required_count": self.matched_required_count,
            "overall_match_ratio": round(self.overall_match_ratio, 2)
        }
