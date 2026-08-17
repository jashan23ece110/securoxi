"""
SECUROXI AI Phase 2 Stage 3 — Skill & Requirement Normalization Models
Dataclasses for canonical skill representations, normalized experience, education,
and certifications.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class NormalizedSkill:
    """Represents a normalized skill with original text, canonical name, and taxonomy category."""
    raw_text: str
    canonical_name: str
    category: str = "General"  # Language, Framework, Tool, Database, Cloud, SoftSkill
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "canonical_name": self.canonical_name,
            "category": self.category,
            "confidence": round(self.confidence, 2)
        }


@dataclass
class NormalizedExperienceRequirement:
    """Normalized experience requirement numerical bounds."""
    raw_text: str
    min_years: float = 0.0
    max_years: Optional[float] = None
    is_preferred: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "min_years": round(self.min_years, 1),
            "max_years": round(self.max_years, 1) if self.max_years is not None else None,
            "is_preferred": self.is_preferred
        }


@dataclass
class NormalizedEducationRequirement:
    """Normalized education degree level and field of study."""
    raw_text: str
    degree_level: str = "NOT_SPECIFIED"  # High School, Associate, Bachelor's, Master's, Doctorate
    field_of_study: str = "NOT_SPECIFIED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "degree_level": self.degree_level,
            "field_of_study": self.field_of_study
        }


@dataclass
class NormalizedCertification:
    """Normalized industry certification."""
    raw_text: str
    canonical_name: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "canonical_name": self.canonical_name
        }


@dataclass
class NormalizedProfile:
    """Container holding normalized skills, experience, education, and certifications."""
    source_id: str
    required_skills: List[NormalizedSkill] = field(default_factory=list)
    preferred_skills: List[NormalizedSkill] = field(default_factory=list)
    experience_requirement: Optional[NormalizedExperienceRequirement] = None
    education_requirement: Optional[NormalizedEducationRequirement] = None
    certifications: List[NormalizedCertification] = field(default_factory=list)

    def canonical_required_skill_names(self) -> List[str]:
        return list(dict.fromkeys(s.canonical_name for s in self.required_skills))

    def canonical_preferred_skill_names(self) -> List[str]:
        return list(dict.fromkeys(s.canonical_name for s in self.preferred_skills))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "required_skills": [s.to_dict() for s in self.required_skills],
            "preferred_skills": [s.to_dict() for s in self.preferred_skills],
            "experience_requirement": self.experience_requirement.to_dict() if self.experience_requirement else None,
            "education_requirement": self.education_requirement.to_dict() if self.education_requirement else None,
            "certifications": [c.to_dict() for c in self.certifications]
        }
