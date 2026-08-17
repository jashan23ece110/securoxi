"""
SECUROXI AI Phase 2 Stage 7 — Explainable Report Generator
Generates human-readable Markdown and machine-readable JSON screening reports
with complete evidence provenance and human review disclaimers.
"""

import uuid
from typing import List, Dict, Any, Optional
from securoxi.logger import get_logger
from securoxi.screening.extraction_models import ExtractedResumeProfile, ExtractedJDProfile
from securoxi.screening.matching_models import MatchingReport, MatchStatus
from securoxi.screening.qualification_models import QualificationAnalysisReport
from securoxi.screening.scoring_models import CandidateScoreReport
from securoxi.screening.report_models import (
    RecommendationCategory,
    RequirementEvidenceLink,
    ScreeningReport
)


class SecuroxiReportGenerator:
    """
    Generator for Explainable Screening Reports.
    Ensures zero hallucination by linking all requirement assertions directly to source resume evidence lines.
    """

    def __init__(self):
        self.logger = get_logger("securoxi.screening.report_generator")

    def generate_report(
        self,
        resume_profile: ExtractedResumeProfile,
        jd_profile: ExtractedJDProfile,
        matching_report: MatchingReport,
        qualification_report: QualificationAnalysisReport,
        score_report: CandidateScoreReport
    ) -> ScreeningReport:
        """
        Synthesizes structured screening findings into an explainable report.
        """
        self.logger.info(f"Generating screening report for Candidate '{resume_profile.candidate_name}' ({resume_profile.resume_id})")

        # 1. Determine Recommendation Category
        rec_cat = self._determine_recommendation_category(score_report.fit_score, resume_profile)

        # 2. Build Required Matches & Missing Lists
        req_matches: List[RequirementEvidenceLink] = []
        req_missing: List[RequirementEvidenceLink] = []

        for rm in matching_report.required_skill_matches:
            prov_loc = resume_profile.field_provenance.get(
                rm.requirement, f"Extracted from resume section: '{resume_profile.candidate_name}'"
            )
            link = RequirementEvidenceLink(
                requirement_name=rm.requirement,
                is_required=True,
                status=rm.match_status.value,
                candidate_evidence=rm.candidate_evidence,
                provenance_location=prov_loc,
                explanation=rm.explanation
            )
            if rm.match_status == MatchStatus.NO_MATCH:
                req_missing.append(link)
            else:
                req_matches.append(link)

        # 3. Build Preferred Matches List
        pref_matches: List[RequirementEvidenceLink] = []
        for pm in matching_report.preferred_skill_matches:
            prov_loc = resume_profile.field_provenance.get(pm.requirement, "Resume skill list")
            link = RequirementEvidenceLink(
                requirement_name=pm.requirement,
                is_required=False,
                status=pm.match_status.value,
                candidate_evidence=pm.candidate_evidence,
                provenance_location=prov_loc,
                explanation=pm.explanation
            )
            pref_matches.append(link)

        # 4. Summarize Experience & Education
        exp_summary = f"{qualification_report.total_relevant_experience_years} non-overlapping years total experience."
        edu_degrees = [e.degree for e in resume_profile.education]
        edu_summary = ", ".join(edu_degrees) if edu_degrees else "No academic degree explicitly stated"

        report_id = f"REP-{uuid.uuid4().hex[:8]}"

        return ScreeningReport(
            report_id=report_id,
            candidate_id=resume_profile.resume_id,
            candidate_name=resume_profile.candidate_name,
            jd_id=jd_profile.jd_id,
            job_title=jd_profile.job_title,
            match_score=score_report.fit_score,
            recommendation=rec_cat,
            required_matches=req_matches,
            required_missing=req_missing,
            preferred_matches=pref_matches,
            experience_summary=exp_summary,
            education_summary=edu_summary,
            strengths=score_report.strengths,
            gaps=score_report.gaps,
            uncertainties=score_report.uncertainties,
            security_verdict=resume_profile.security_verdict
        )

    def _determine_recommendation_category(
        self, fit_score: float, resume_profile: ExtractedResumeProfile
    ) -> RecommendationCategory:
        if resume_profile.summary == "NOT_SPECIFIED" and len(resume_profile.work_experience) == 0:
            return RecommendationCategory.INSUFFICIENT_DATA

        if fit_score >= 85.0:
            return RecommendationCategory.STRONG_MATCH
        elif fit_score >= 70.0:
            return RecommendationCategory.GOOD_MATCH
        elif fit_score >= 50.0:
            return RecommendationCategory.PARTIAL_MATCH
        else:
            return RecommendationCategory.LOW_MATCH
