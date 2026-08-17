"""
SECUROXI AI Phase 2 Stage 2 — Structured Information Extraction Models
Dataclasses for extracted Resume profiles and Job Description requirements.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class EducationRecord:
    """Represents a single education degree or academic achievement."""
    degree: str = "UNKNOWN"
    field_of_study: str = "NOT_SPECIFIED"
    institution: str = "NOT_SPECIFIED"
    graduation_year: Optional[int] = None
    provenance: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "degree": self.degree,
            "field_of_study": self.field_of_study,
            "institution": self.institution,
            "graduation_year": self.graduation_year,
            "provenance": self.provenance
        }


@dataclass
class ExperienceRecord:
    """Represents a single employment or work experience position."""
    job_title: str = "UNKNOWN"
    company: str = "NOT_SPECIFIED"
    start_date: str = "NOT_SPECIFIED"
    end_date: str = "NOT_SPECIFIED"
    duration_years: float = 0.0
    responsibilities: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    provenance: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_title": self.job_title,
            "company": self.company,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "duration_years": round(self.duration_years, 1),
            "responsibilities": self.responsibilities,
            "achievements": self.achievements,
            "provenance": self.provenance
        }


@dataclass
class ProjectRecord:
    """Represents a technical project or portfolio item."""
    title: str = "UNKNOWN"
    technologies: List[str] = field(default_factory=list)
    description: str = "NOT_SPECIFIED"
    provenance: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "technologies": self.technologies,
            "description": self.description,
            "provenance": self.provenance
        }


@dataclass
class CategorizedSkills:
    """Categorized technical and professional skill taxonomy."""
    programming_languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    databases: List[str] = field(default_factory=list)
    cloud_platforms: List[str] = field(default_factory=list)
    general_technical: List[str] = field(default_factory=list)

    def all_skills(self) -> List[str]:
        combined = (
            self.programming_languages +
            self.frameworks +
            self.tools +
            self.databases +
            self.cloud_platforms +
            self.general_technical
        )
        return list(dict.fromkeys(combined)) # Remove duplicates while preserving order

    def to_dict(self) -> Dict[str, Any]:
        return {
            "programming_languages": self.programming_languages,
            "frameworks": self.frameworks,
            "tools": self.tools,
            "databases": self.databases,
            "cloud_platforms": self.cloud_platforms,
            "general_technical": self.general_technical,
            "all_skills_count": len(self.all_skills())
        }


@dataclass
class ExtractedResumeProfile:
    """Comprehensive structured profile extracted from a candidate Resume."""
    resume_id: str
    candidate_name: str = "UNKNOWN"
    summary: str = "NOT_SPECIFIED"
    skills: CategorizedSkills = field(default_factory=CategorizedSkills)
    education: List[EducationRecord] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    work_experience: List[ExperienceRecord] = field(default_factory=list)
    projects: List[ProjectRecord] = field(default_factory=list)
    total_years_experience: float = 0.0
    extraction_confidence: float = 0.90
    security_verdict: str = "SAFE"
    field_provenance: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resume_id": self.resume_id,
            "candidate_name": self.candidate_name,
            "summary": self.summary,
            "skills": self.skills.to_dict(),
            "education": [e.to_dict() for e in self.education],
            "certifications": self.certifications,
            "work_experience": [w.to_dict() for w in self.work_experience],
            "projects": [p.to_dict() for p in self.projects],
            "total_years_experience": round(self.total_years_experience, 1),
            "extraction_confidence": round(self.extraction_confidence, 2),
            "security_verdict": self.security_verdict,
            "field_provenance": self.field_provenance
        }



@dataclass
class ExtractedJDProfile:
    """Comprehensive structured profile extracted from a Job Description."""
    jd_id: str
    job_title: str = "UNKNOWN"
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    minimum_experience_years: float = 0.0
    education_requirements: str = "NOT_SPECIFIED"
    certifications_required: List[str] = field(default_factory=list)
    responsibilities: List[str] = field(default_factory=list)
    technologies_and_tools: List[str] = field(default_factory=list)
    location_requirements: str = "NOT_SPECIFIED"
    employment_type: str = "NOT_SPECIFIED"
    explicit_constraints: List[str] = field(default_factory=list)
    extraction_confidence: float = 0.90
    field_provenance: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "jd_id": self.jd_id,
            "job_title": self.job_title,
            "required_skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "minimum_experience_years": round(self.minimum_experience_years, 1),
            "education_requirements": self.education_requirements,
            "certifications_required": self.certifications_required,
            "responsibilities": self.responsibilities,
            "technologies_and_tools": self.technologies_and_tools,
            "location_requirements": self.location_requirements,
            "employment_type": self.employment_type,
            "explicit_constraints": self.explicit_constraints,
            "extraction_confidence": round(self.extraction_confidence, 2),
            "field_provenance": self.field_provenance
        }
