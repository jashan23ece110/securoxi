"""
SECUROXI AI Phase 2 Stage 7 — Explainable Screening Report Models
Dataclasses for evidence provenance links, human-readable markdown reports,
and machine-readable JSON screening reports.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class RecommendationCategory(str, Enum):
    STRONG_MATCH = "STRONG_MATCH"
    GOOD_MATCH = "GOOD_MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    LOW_MATCH = "LOW_MATCH"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass
class RequirementEvidenceLink:
    """Links a job requirement to candidate resume evidence with provenance location."""
    requirement_name: str
    is_required: bool
    status: str  # MATCH, PARTIAL_MATCH, NO_MATCH
    candidate_evidence: str
    provenance_location: str
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirement_name": self.requirement_name,
            "is_required": self.is_required,
            "status": self.status,
            "candidate_evidence": self.candidate_evidence,
            "provenance_location": self.provenance_location,
            "explanation": self.explanation
        }


@dataclass
class ScreeningReport:
    """Comprehensive explainable screening report with evidence provenance and human review disclaimers."""
    report_id: str
    candidate_id: str
    candidate_name: str
    jd_id: str
    job_title: str
    match_score: float
    recommendation: RecommendationCategory
    required_matches: List[RequirementEvidenceLink] = field(default_factory=list)
    required_missing: List[RequirementEvidenceLink] = field(default_factory=list)
    preferred_matches: List[RequirementEvidenceLink] = field(default_factory=list)
    experience_summary: str = ""
    education_summary: str = ""
    strengths: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    security_verdict: str = "SAFE"
    human_review_disclaimer: str = (
        "IMPORTANT NOTICE: This report provides automated evidence analysis to assist human recruiters "
        "and hiring managers. It does not constitute an automated hiring or rejection decision."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "jd_id": self.jd_id,
            "job_title": self.job_title,
            "match_score": round(self.match_score, 1),
            "recommendation": self.recommendation.value,
            "required_matches": [r.to_dict() for r in self.required_matches],
            "required_missing": [m.to_dict() for m in self.required_missing],
            "preferred_matches": [p.to_dict() for p in self.preferred_matches],
            "experience_summary": self.experience_summary,
            "education_summary": self.education_summary,
            "strengths": self.strengths,
            "gaps": self.gaps,
            "uncertainties": self.uncertainties,
            "security_verdict": self.security_verdict,
            "human_review_disclaimer": self.human_review_disclaimer
        }

    def to_markdown(self) -> str:
        """Generates a human-readable Markdown screening report."""
        md = []
        md.append(f"# SECUROXI Candidate Screening Report — {self.candidate_name}")
        md.append(f"**Report ID**: `{self.report_id}` | **Target Role**: {self.job_title}")
        md.append(f"**Security Verdict**: `{self.security_verdict}`")
        md.append(f"**Match Score**: **{round(self.match_score, 1)} / 100** ({self.recommendation.value})\n")

        md.append(f"> **Notice**: {self.human_review_disclaimer}\n")

        md.append("## Executive Summary")
        md.append(f"* **Relevant Experience**: {self.experience_summary}")
        md.append(f"* **Education Profile**: {self.education_summary}\n")

        md.append("## Key Candidate Strengths")
        if self.strengths:
            for s in self.strengths:
                md.append(f"* ✅ {s}")
        else:
            md.append("* None identified")
        md.append("")

        md.append("## Requirement Gaps & Missing Skills")
        if self.gaps:
            for g in self.gaps:
                md.append(f"* ⚠️ {g}")
        else:
            md.append("* No critical gaps identified")
        md.append("")

        md.append("## Detailed Evidence Provenance")
        md.append("### Required Requirements Matched")
        for rm in self.required_matches:
            md.append(f"- **{rm.requirement_name}**: `{rm.status}`")
            md.append(f"  - *Candidate Evidence*: {rm.candidate_evidence}")
            md.append(f"  - *Provenance Location*: {rm.provenance_location}")

        if self.required_missing:
            md.append("\n### Required Requirements Missing")
            for mis in self.required_missing:
                md.append(f"- **{mis.requirement_name}**: `NO_MATCH`")
                md.append(f"  - *Explanation*: {mis.explanation}")

        return "\n".join(md)
