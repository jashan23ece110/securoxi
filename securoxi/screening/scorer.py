"""
SECUROXI AI Phase 2 Stage 6 — Candidate Scorer & Ranking Engine
Calculates explainable candidate fit scores and ranks multiple candidates against Job Descriptions.
Enforces heavy penalty ceilings for missing mandatory skills.
"""

from typing import List, Dict, Any, Tuple, Optional

from securoxi.logger import get_logger
from securoxi.screening.models import ResumeDocument, JobDescriptionDocument
from securoxi.screening.extraction_models import ExtractedResumeProfile, ExtractedJDProfile
from securoxi.screening.matching_engine import SecuroxiMatchingEngine
from securoxi.screening.matching_models import MatchingReport, MatchStatus
from securoxi.screening.qualification_analyzer import SecuroxiQualificationAnalyzer
from securoxi.screening.qualification_models import QualificationAnalysisReport, QualificationStatus
from securoxi.screening.scoring_models import ScoringWeights, CandidateScoreReport, RankedCandidatesReport
from securoxi.screening.ingestion import SecuroxiIngestionEngine
from securoxi.screening.extractor import RuleBasedExtractor


class SecuroxiCandidateScorer:
    """
    Explainable Candidate Fit Scorer.
    Calculates transparent fit scores based on required skills, experience, preferred skills, and degree qualifications.
    """

    def __init__(self, weights: Optional[ScoringWeights] = None):
        self.logger = get_logger("securoxi.screening.scorer")
        self.weights = weights or ScoringWeights()

    def score_candidate(
        self,
        resume_profile: ExtractedResumeProfile,
        jd_profile: ExtractedJDProfile,
        matching_report: MatchingReport,
        qualification_report: QualificationAnalysisReport
    ) -> CandidateScoreReport:
        """
        Calculates explainable fit score and requirement breakdown for a candidate.
        """
        self.logger.info(f"Scoring candidate '{resume_profile.candidate_name}' ({resume_profile.resume_id}) against JD '{jd_profile.jd_id}'")

        # 1. Calculate Component Scores
        req_score = self._calculate_required_skills_score(matching_report)
        exp_score = self._calculate_experience_score(qualification_report, jd_profile)
        pref_score = self._calculate_preferred_skills_score(matching_report)
        edu_cert_score = self._calculate_education_cert_score(qualification_report)

        # 2. Weighted Sum Calculation
        raw_fit_score = (
            (req_score * self.weights.required_skills_weight) +
            (exp_score * self.weights.experience_weight) +
            (pref_score * self.weights.preferred_skills_weight) +
            (edu_cert_score * self.weights.education_cert_weight)
        )

        # 3. Apply Mandatory Missing Penalty Ceiling
        has_missing_required = any(
            m.match_status in [MatchStatus.NO_MATCH, MatchStatus.UNKNOWN]
            for m in matching_report.required_skill_matches
        )

        if has_missing_required:
            final_fit_score = min(raw_fit_score, self.weights.mandatory_missing_penalty_ceiling)
        else:
            final_fit_score = raw_fit_score

        # 4. Categorize Fit Level
        if final_fit_score >= 85.0:
            category = "EXCELLENT_FIT"
        elif final_fit_score >= 70.0:
            category = "STRONG_FIT"
        elif final_fit_score >= 50.0:
            category = "PARTIAL_FIT"
        else:
            category = "WEAK_FIT"

        # 5. Extract Strengths, Gaps, and Uncertainties
        strengths, gaps, uncertainties = self._extract_strengths_and_gaps(
            matching_report, qualification_report, resume_profile
        )

        breakdown = {
            "required_skills_score": req_score,
            "experience_score": exp_score,
            "preferred_skills_score": pref_score,
            "education_cert_score": edu_cert_score,
            "raw_weighted_score": raw_fit_score
        }

        verdict_str = resume_profile.security_verdict if hasattr(resume_profile, "security_verdict") else "SAFE"


        return CandidateScoreReport(
            candidate_id=resume_profile.resume_id,
            candidate_name=resume_profile.candidate_name,
            jd_id=jd_profile.jd_id,
            fit_score=final_fit_score,
            fit_category=category,
            score_breakdown=breakdown,
            strengths=strengths,
            gaps=gaps,
            uncertainties=uncertainties,
            security_verdict=verdict_str
        )

    def _calculate_required_skills_score(self, report: MatchingReport) -> float:
        if not report.required_skill_matches:
            return 100.0

        points = 0.0
        for match in report.required_skill_matches:
            if match.match_status == MatchStatus.MATCH:
                points += 100.0
            elif match.match_status == MatchStatus.PARTIAL_MATCH:
                points += 50.0

        return points / len(report.required_skill_matches)

    def _calculate_experience_score(
        self, qual_report: QualificationAnalysisReport, jd_profile: ExtractedJDProfile
    ) -> float:
        req_years = jd_profile.minimum_experience_years
        cand_years = qual_report.total_relevant_experience_years

        if req_years == 0.0:
            return 100.0

        ratio = cand_years / req_years
        return min(ratio * 100.0, 100.0)

    def _calculate_preferred_skills_score(self, report: MatchingReport) -> float:
        if not report.preferred_skill_matches:
            return 100.0

        points = 0.0
        for match in report.preferred_skill_matches:
            if match.match_status == MatchStatus.MATCH:
                points += 100.0
            elif match.match_status == MatchStatus.PARTIAL_MATCH:
                points += 50.0

        return points / len(report.preferred_skill_matches)

    def _calculate_education_cert_score(self, qual_report: QualificationAnalysisReport) -> float:
        edu_cert_findings = [
            f for f in qual_report.findings
            if "Education" in f.qualification_name or "Certifications" in f.qualification_name
        ]

        if not edu_cert_findings:
            return 100.0

        points = 0.0
        for f in edu_cert_findings:
            if f.status == QualificationStatus.REQUIREMENT_MET:
                points += 100.0
            elif f.status == QualificationStatus.REQUIREMENT_PARTIAL:
                points += 50.0

        return points / len(edu_cert_findings)

    def _extract_strengths_and_gaps(
        self,
        matching_report: MatchingReport,
        qual_report: QualificationAnalysisReport,
        resume_profile: ExtractedResumeProfile
    ) -> Tuple[List[str], List[str], List[str]]:
        strengths: List[str] = []
        gaps: List[str] = []
        uncertainties: List[str] = []

        for m in matching_report.required_skill_matches:
            if m.match_status == MatchStatus.MATCH:
                strengths.append(f"Satisfies mandatory skill requirement '{m.requirement}' ({m.candidate_evidence})")
            elif m.match_status == MatchStatus.NO_MATCH:
                gaps.append(f"Missing mandatory required skill '{m.requirement}'")
            elif m.match_status == MatchStatus.PARTIAL_MATCH:
                gaps.append(f"Partial match for skill '{m.requirement}' ({m.explanation})")

        for p in matching_report.preferred_skill_matches:
            if p.match_status == MatchStatus.MATCH:
                strengths.append(f"Possesses preferred skill '{p.requirement}'")

        if qual_report.total_relevant_experience_years > 0:
            strengths.append(f"Demonstrates {qual_report.total_relevant_experience_years} years relevant career experience")

        if resume_profile.summary == "NOT_SPECIFIED":
            uncertainties.append("Resume lacks an explicit summary section")

        return strengths[:5], gaps[:5], uncertainties[:3]


class SecuroxiRankingEngine:
    """
    Ranks multiple candidate resume profiles against a single Job Description requirement.
    """

    def __init__(self, weights: Optional[ScoringWeights] = None):
        self.logger = get_logger("securoxi.screening.ranking")
        self.weights = weights or ScoringWeights()
        self.ingestion_engine = SecuroxiIngestionEngine()
        self.extractor = RuleBasedExtractor()
        self.matching_engine = SecuroxiMatchingEngine()
        self.qualification_analyzer = SecuroxiQualificationAnalyzer()
        self.scorer = SecuroxiCandidateScorer(weights=self.weights)

    def rank_candidates(
        self, resume_paths: List[str], jd_source: Any
    ) -> RankedCandidatesReport:
        """
        Ingest, extract, match, score, and rank multiple candidate resume paths against a JD.
        """
        self.logger.info(f"Ranking {len(resume_paths)} candidate resumes against Job Description")

        # 1. Ingest & Extract JD
        jd_doc = self.ingestion_engine.ingest_job_description(jd_source)
        jd_prof = self.extractor.extract_jd_profile(jd_doc)

        scored_candidates: List[CandidateScoreReport] = []

        # 2. Process each resume
        for pdf_path in resume_paths:
            try:
                resume_doc = self.ingestion_engine.ingest_resume(pdf_path)
                resume_prof = self.extractor.extract_resume_profile(resume_doc)
                match_report = self.matching_engine.match_resume_to_jd(resume_prof, jd_prof)
                qual_report = self.qualification_analyzer.analyze_qualifications(resume_prof, jd_prof)
                candidate_score = self.scorer.score_candidate(
                    resume_prof, jd_prof, match_report, qual_report
                )
                scored_candidates.append(candidate_score)
            except Exception as err:
                self.logger.error(f"Failed processing candidate resume '{pdf_path}': {err}")

        # 3. Sort candidates descending by fit_score
        scored_candidates.sort(key=lambda c: c.fit_score, reverse=True)

        return RankedCandidatesReport(
            jd_id=jd_prof.jd_id,
            job_title=jd_prof.job_title,
            total_candidates=len(scored_candidates),
            ranked_candidates=scored_candidates,
            weights_used=self.weights
        )
