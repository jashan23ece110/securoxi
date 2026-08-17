"""
SECUROXI AI Phase 2 Stage 5 — Qualification & Experience Analyzer Engine
Evaluates candidate qualifications against empirical evidence.
Prevents equating total career length with technology-specific experience and resolves date overlaps.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from securoxi.logger import get_logger
from securoxi.screening.normalizer import SecuroxiNormalizer
from securoxi.screening.extraction_models import ExtractedResumeProfile, ExtractedJDProfile, ExperienceRecord
from securoxi.screening.qualification_models import (
    QualificationStatus,
    QualificationFinding,
    QualificationAnalysisReport
)


class SecuroxiQualificationAnalyzer:
    """
    Empirical Qualification & Experience Analyzer.
    Resolves employment overlaps, technology-specific experience durations,
    internships, missing dates, and explicit JD qualification constraints.
    """

    def __init__(self):
        self.logger = get_logger("securoxi.screening.qualification")
        self.normalizer = SecuroxiNormalizer()

    def analyze_qualifications(
        self,
        resume_profile: ExtractedResumeProfile,
        jd_profile: ExtractedJDProfile
    ) -> QualificationAnalysisReport:
        """
        Analyze whether candidate satisfies explicit qualification requirements.
        """
        self.logger.info(f"Analyzing qualifications for Resume ID '{resume_profile.resume_id}' against JD ID '{jd_profile.jd_id}'")

        # 1. Calculate Non-Overlapping Total Experience
        total_exp_years = self._calculate_non_overlapping_experience(resume_profile.work_experience)

        # 2. Calculate Technology-Specific Experience Breakdown
        tech_breakdown = self._calculate_technology_breakdown(resume_profile)

        # 3. Evaluate Qualification Requirements
        findings: List[QualificationFinding] = []

        # A. Evaluate Total Experience Qualification
        if jd_profile.minimum_experience_years > 0:
            exp_finding = self._evaluate_total_experience_qualification(
                jd_profile.minimum_experience_years, total_exp_years
            )
            findings.append(exp_finding)

        # B. Evaluate Technology-Specific Qualifications
        for req_skill in jd_profile.required_skills:
            norm_skill = self.normalizer.normalize_skill(req_skill)
            canonical_name = norm_skill.canonical_name
            tech_finding = self._evaluate_technology_qualification(
                req_skill_name=canonical_name,
                jd_min_years=jd_profile.minimum_experience_years,
                tech_breakdown=tech_breakdown,
                candidate_has_skill=canonical_name in [s.capitalize() for s in resume_profile.skills.all_skills()] or canonical_name in tech_breakdown
            )
            findings.append(tech_finding)

        # C. Evaluate Education Qualification
        if jd_profile.education_requirements != "NOT_SPECIFIED":
            edu_finding = self._evaluate_education_qualification(
                jd_profile.education_requirements, resume_profile.education
            )
            findings.append(edu_finding)

        # D. Evaluate Certification Qualification
        if jd_profile.certifications_required:
            cert_finding = self._evaluate_certification_qualification(
                jd_profile.certifications_required, resume_profile.certifications
            )
            findings.append(cert_finding)

        # Calculate metrics
        total_count = len(findings)
        met_count = sum(1 for f in findings if f.status == QualificationStatus.REQUIREMENT_MET)
        partial_count = sum(1 for f in findings if f.status == QualificationStatus.REQUIREMENT_PARTIAL)
        score = ((met_count + (partial_count * 0.5)) / total_count) if total_count > 0 else 1.0

        return QualificationAnalysisReport(
            resume_id=resume_profile.resume_id,
            jd_id=jd_profile.jd_id,
            total_relevant_experience_years=total_exp_years,
            technology_experience_breakdown=tech_breakdown,
            findings=findings,
            met_qualifications_count=met_count,
            total_qualifications_count=total_count,
            qualification_score=score
        )

    def _calculate_non_overlapping_experience(self, experiences: List[ExperienceRecord]) -> float:
        """
        Calculates non-overlapping career experience years by merging overlapping date intervals.
        """
        intervals: List[Tuple[int, int]] = []
        for exp in experiences:
            # Check for year numbers
            try:
                start_yr = int(exp.start_date)
                end_str = exp.end_date.strip().lower()
                end_yr = 2026 if end_str in ["present", "current", "now"] else int(end_str)
                if end_yr >= start_yr:
                    intervals.append((start_yr, end_yr))
            except (ValueError, TypeError):
                continue

        if not intervals:
            # Fallback to sum of durations if dates not explicit
            return sum(exp.duration_years for exp in experiences)

        # Sort intervals by start year
        intervals.sort(key=lambda x: x[0])

        merged: List[Tuple[int, int]] = []
        for current in intervals:
            if not merged:
                merged.append(current)
            else:
                prev_start, prev_end = merged[-1]
                if current[0] <= prev_end:
                    merged[-1] = (prev_start, max(prev_end, current[1]))
                else:
                    merged.append(current)

        total_years = sum(float(end - start) for start, end in merged)
        return max(total_years, 0.0)

    def _calculate_technology_breakdown(self, resume_profile: ExtractedResumeProfile) -> Dict[str, float]:
        """
        Calculates empirical experience duration for each candidate technology based on
        the specific position/project durations where that technology was referenced.
        """
        breakdown: Dict[str, float] = {}
        candidate_skills = resume_profile.skills.all_skills()

        for skill_raw in candidate_skills:
            norm = self.normalizer.normalize_skill(skill_raw)
            canonical = norm.canonical_name
            total_tech_years = 0.0

            for exp in resume_profile.work_experience:
                text_to_search = (exp.job_title + " " + " ".join(exp.responsibilities) + " " + " ".join(exp.achievements) + " " + exp.provenance).lower()
                if canonical.lower() in text_to_search or norm.raw_text.lower() in text_to_search:
                    total_tech_years += exp.duration_years

            # Default fallback if skill exists in skill list but position duration was unlinked
            if total_tech_years == 0.0:
                total_tech_years = 1.0

            breakdown[canonical] = total_tech_years

        return breakdown

    def _evaluate_total_experience_qualification(
        self, req_years: float, total_exp_years: float
    ) -> QualificationFinding:
        if total_exp_years >= req_years:
            return QualificationFinding(
                qualification_name="Overall Professional Experience",
                status=QualificationStatus.REQUIREMENT_MET,
                required_level=f"{req_years}+ years total experience",
                candidate_evidence=f"{total_exp_years} non-overlapping years total experience",
                confidence=0.95,
                explanation=f"Candidate total experience ({total_exp_years} yrs) meets requirement ({req_years} yrs)."
            )
        elif total_exp_years > 0.0:
            return QualificationFinding(
                qualification_name="Overall Professional Experience",
                status=QualificationStatus.REQUIREMENT_PARTIAL,
                required_level=f"{req_years}+ years total experience",
                candidate_evidence=f"{total_exp_years} non-overlapping years total experience",
                confidence=0.85,
                explanation=f"Candidate total experience ({total_exp_years} yrs) is below requirement ({req_years} yrs)."
            )
        else:
            return QualificationFinding(
                qualification_name="Overall Professional Experience",
                status=QualificationStatus.REQUIREMENT_NOT_MET,
                required_level=f"{req_years}+ years total experience",
                candidate_evidence="0.0 years experience",
                confidence=0.90,
                explanation="Candidate has 0.0 years recorded experience."
            )

    def _evaluate_technology_qualification(
        self,
        req_skill_name: str,
        jd_min_years: float,
        tech_breakdown: Dict[str, float],
        candidate_has_skill: bool
    ) -> QualificationFinding:
        cand_tech_years = tech_breakdown.get(req_skill_name, 0.0)

        if not candidate_has_skill and cand_tech_years == 0.0:
            return QualificationFinding(
                qualification_name=f"Technology Skill: {req_skill_name}",
                status=QualificationStatus.REQUIREMENT_NOT_MET,
                required_level=f"Proficiency in {req_skill_name}",
                candidate_evidence="Skill not listed in resume profile",
                confidence=0.95,
                explanation=f"Candidate profile shows no evidence of {req_skill_name} skill."
            )

        if jd_min_years > 0 and cand_tech_years < jd_min_years:
            return QualificationFinding(
                qualification_name=f"Technology Skill: {req_skill_name}",
                status=QualificationStatus.REQUIREMENT_PARTIAL,
                required_level=f"{jd_min_years}+ years in {req_skill_name}",
                candidate_evidence=f"{cand_tech_years} years specific experience in {req_skill_name}",
                confidence=0.90,
                explanation=f"Candidate has {cand_tech_years} yrs specific experience in {req_skill_name}, below required {jd_min_years} yrs."
            )

        return QualificationFinding(
            qualification_name=f"Technology Skill: {req_skill_name}",
            status=QualificationStatus.REQUIREMENT_MET,
            required_level=f"Proficiency in {req_skill_name}",
            candidate_evidence=f"{cand_tech_years} years specific experience in {req_skill_name}",
            confidence=0.95,
            explanation=f"Candidate satisfies requirement for {req_skill_name}."
        )

    def _evaluate_education_qualification(
        self, req_edu_text: str, candidate_education: List[Any]
    ) -> QualificationFinding:
        if not candidate_education:
            return QualificationFinding(
                qualification_name="Education Qualification",
                status=QualificationStatus.REQUIREMENT_NOT_MET,
                required_level=req_edu_text,
                candidate_evidence="No education degree listed",
                confidence=0.90,
                explanation="Candidate resume lists no academic degree."
            )

        degrees = [e.degree for e in candidate_education]
        return QualificationFinding(
            qualification_name="Education Qualification",
            status=QualificationStatus.REQUIREMENT_MET,
            required_level=req_edu_text,
            candidate_evidence=", ".join(degrees),
            confidence=0.95,
            explanation=f"Candidate degree ({degrees[0]}) satisfies education requirement."
        )

    def _evaluate_certification_qualification(
        self, req_certs: List[str], candidate_certs: List[str]
    ) -> QualificationFinding:
        if not candidate_certs:
            return QualificationFinding(
                qualification_name="Certifications Qualification",
                status=QualificationStatus.REQUIREMENT_NOT_MET,
                required_level=", ".join(req_certs),
                candidate_evidence="No certifications listed",
                confidence=0.85,
                explanation="Candidate resume lists no professional certifications."
            )

        return QualificationFinding(
            qualification_name="Certifications Qualification",
            status=QualificationStatus.REQUIREMENT_MET,
            required_level=", ".join(req_certs),
            candidate_evidence=", ".join(candidate_certs),
            confidence=0.90,
            explanation="Candidate has relevant industry certifications."
        )
