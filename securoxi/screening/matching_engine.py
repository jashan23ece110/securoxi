"""
SECUROXI AI Phase 2 Stage 4 — Semantic Matching Engine
Compares structured candidate resume profiles against JD requirements.
Evaluates exact, normalized, semantic related, missing, and experience matches.
"""

from typing import List, Dict, Any, Tuple, Optional
from securoxi.logger import get_logger
from securoxi.screening.normalizer import SecuroxiNormalizer
from securoxi.screening.extraction_models import ExtractedResumeProfile, ExtractedJDProfile
from securoxi.screening.matching_models import (
    MatchStatus,
    MatchType,
    RequirementMatch,
    MatchingReport
)


# Related Technology Ontology Map for Semantic Matching
RELATED_TECH_MAP: Dict[str, Dict[str, Any]] = {
    "PostgreSQL": {
        "related": ["MySQL", "SQLite", "MongoDB", "Redis"],
        "confidence": 0.70,
        "note": "Related database technology"
    },
    "MySQL": {
        "related": ["PostgreSQL", "SQLite", "MySQL"],
        "confidence": 0.70,
        "note": "Related relational database"
    },
    "PyTorch": {
        "related": ["TensorFlow", "Keras"],
        "confidence": 0.70,
        "note": "Related deep learning framework"
    },
    "TensorFlow": {
        "related": ["PyTorch", "Keras"],
        "confidence": 0.70,
        "note": "Related deep learning framework"
    },
    "AWS": {
        "related": ["GCP", "Azure", "Cloudflare"],
        "confidence": 0.65,
        "note": "Related cloud platform provider"
    },
    "GCP": {
        "related": ["AWS", "Azure"],
        "confidence": 0.65,
        "note": "Related cloud platform provider"
    },
    "React": {
        "related": ["React Native", "Vue", "Angular"],
        "confidence": 0.60,
        "note": "React web framework is related to React Native / Vue, but is not an exact match"
    },
    "React Native": {
        "related": ["React", "Flutter"],
        "confidence": 0.60,
        "note": "React Native mobile framework is related to React web framework, but is not an exact match"
    },
    "FastAPI": {
        "related": ["Flask", "Django"],
        "confidence": 0.75,
        "note": "Related Python web framework"
    },
    "Flask": {
        "related": ["FastAPI", "Django"],
        "confidence": 0.75,
        "note": "Related Python web framework"
    }
}


class SecuroxiMatchingEngine:
    """
    Requirement-Level Semantic Matching Engine.
    Enforces strict distinction between exact/normalized matches and partial semantic matches.
    """

    def __init__(self):
        self.logger = get_logger("securoxi.screening.matching")
        self.normalizer = SecuroxiNormalizer()

    def match_resume_to_jd(
        self,
        resume_profile: ExtractedResumeProfile,
        jd_profile: ExtractedJDProfile
    ) -> MatchingReport:
        """
        Compare candidate resume profile against job description requirements.
        Generates requirement-level match evaluations.
        """
        self.logger.info(f"Matching Resume ID '{resume_profile.resume_id}' against JD ID '{jd_profile.jd_id}'")

        # 1. Normalize Candidate Skills
        candidate_raw_skills = resume_profile.skills.all_skills()
        candidate_norm_skills = self.normalizer.normalize_skills_list(candidate_raw_skills)
        candidate_canonical_map = {s.canonical_name: s for s in candidate_norm_skills}

        # 2. Evaluate Required Skills
        req_matches: List[RequirementMatch] = []
        for req_skill in jd_profile.required_skills:
            match = self._evaluate_skill_requirement(req_skill, is_required=True, candidate_map=candidate_canonical_map, candidate_raw=candidate_raw_skills)
            req_matches.append(match)

        # 3. Evaluate Preferred Skills
        pref_matches: List[RequirementMatch] = []
        for pref_skill in jd_profile.preferred_skills:
            match = self._evaluate_skill_requirement(pref_skill, is_required=False, candidate_map=candidate_canonical_map, candidate_raw=candidate_raw_skills)
            pref_matches.append(match)

        # 4. Evaluate Experience Match
        exp_match = self._evaluate_experience(resume_profile, jd_profile)

        # 5. Evaluate Education Match
        edu_match = self._evaluate_education(resume_profile, jd_profile)

        # Calculate summary metrics
        total_req = len(req_matches)
        matched_req = sum(1 for m in req_matches if m.match_status in [MatchStatus.MATCH, MatchStatus.PARTIAL_MATCH])
        overall_ratio = (matched_req / total_req) if total_req > 0 else 1.0

        return MatchingReport(
            resume_id=resume_profile.resume_id,
            jd_id=jd_profile.jd_id,
            required_skill_matches=req_matches,
            preferred_skill_matches=pref_matches,
            experience_match=exp_match,
            education_match=edu_match,
            total_required_count=total_req,
            matched_required_count=matched_req,
            overall_match_ratio=overall_ratio
        )

    def _evaluate_skill_requirement(
        self,
        jd_skill_text: str,
        is_required: bool,
        candidate_map: Dict[str, Any],
        candidate_raw: List[str]
    ) -> RequirementMatch:
        """Evaluates a single skill requirement against candidate skills."""
        jd_norm = self.normalizer.normalize_skill(jd_skill_text)
        canonical_target = jd_norm.canonical_name

        # 1. Exact / Normalized Match
        if canonical_target in candidate_map:
            cand_skill = candidate_map[canonical_target]
            if cand_skill.raw_text.lower() == jd_skill_text.lower():
                return RequirementMatch(
                    requirement=jd_skill_text,
                    is_required=is_required,
                    candidate_evidence=f"Explicit skill: '{cand_skill.raw_text}'",
                    match_status=MatchStatus.MATCH,
                    match_type=MatchType.EXACT_MATCH,
                    confidence=1.0,
                    explanation=f"Exact match on skill '{canonical_target}'"
                )
            else:
                return RequirementMatch(
                    requirement=jd_skill_text,
                    is_required=is_required,
                    candidate_evidence=f"Normalized alias skill: '{cand_skill.raw_text}' -> '{canonical_target}'",
                    match_status=MatchStatus.MATCH,
                    match_type=MatchType.NORMALIZED_MATCH,
                    confidence=0.95,
                    explanation=f"Normalized alias match for target skill '{canonical_target}'"
                )

        # 2. Semantic Related Technology Match
        if canonical_target in RELATED_TECH_MAP:
            rel_info = RELATED_TECH_MAP[canonical_target]
            for rel_tech in rel_info["related"]:
                if rel_tech in candidate_map:
                    found_cand = candidate_map[rel_tech]
                    return RequirementMatch(
                        requirement=jd_skill_text,
                        is_required=is_required,
                        candidate_evidence=f"Related technology: '{found_cand.raw_text}' ({rel_tech})",
                        match_status=MatchStatus.PARTIAL_MATCH,
                        match_type=MatchType.SEMANTIC_RELATED,
                        confidence=rel_info["confidence"],
                        explanation=f"Partial semantic match: {rel_info['note']}"
                    )

        # 3. No Match
        return RequirementMatch(
            requirement=jd_skill_text,
            is_required=is_required,
            candidate_evidence="NONE_FOUND",
            match_status=MatchStatus.NO_MATCH,
            match_type=MatchType.NO_MATCH,
            confidence=0.90,
            explanation=f"Candidate profile does not contain required skill '{canonical_target}'"
        )

    def _evaluate_experience(
        self,
        resume_profile: ExtractedResumeProfile,
        jd_profile: ExtractedJDProfile
    ) -> RequirementMatch:
        """Compares candidate total years of experience against JD minimum requirement."""
        req_years = jd_profile.minimum_experience_years
        cand_years = resume_profile.total_years_experience

        if req_years == 0.0:
            return RequirementMatch(
                requirement="Minimum Experience",
                is_required=False,
                candidate_evidence=f"{cand_years} years total experience",
                match_status=MatchStatus.MATCH,
                match_type=MatchType.EXPERIENCE_MATCH,
                confidence=1.0,
                explanation="No explicit minimum experience required by JD."
            )

        if cand_years >= req_years:
            return RequirementMatch(
                requirement=f"{req_years}+ years experience",
                is_required=True,
                candidate_evidence=f"{cand_years} years total experience",
                match_status=MatchStatus.MATCH,
                match_type=MatchType.EXPERIENCE_MATCH,
                confidence=0.95,
                explanation=f"Candidate experience ({cand_years} yrs) meets or exceeds requirement ({req_years} yrs)."
            )
        elif cand_years > 0.0:
            return RequirementMatch(
                requirement=f"{req_years}+ years experience",
                is_required=True,
                candidate_evidence=f"{cand_years} years total experience",
                match_status=MatchStatus.PARTIAL_MATCH,
                match_type=MatchType.EXPERIENCE_MATCH,
                confidence=0.70,
                explanation=f"Candidate experience ({cand_years} yrs) is below minimum requirement ({req_years} yrs)."
            )
        else:
            return RequirementMatch(
                requirement=f"{req_years}+ years experience",
                is_required=True,
                candidate_evidence="0.0 years experience",
                match_status=MatchStatus.NO_MATCH,
                match_type=MatchType.NO_MATCH,
                confidence=0.90,
                explanation=f"Candidate experience (0.0 yrs) does not meet requirement ({req_years} yrs)."
            )

    def _evaluate_education(
        self,
        resume_profile: ExtractedResumeProfile,
        jd_profile: ExtractedJDProfile
    ) -> RequirementMatch:
        """Compares candidate education records against JD education requirement."""
        req_edu = jd_profile.education_requirements
        if req_edu == "NOT_SPECIFIED":
            return RequirementMatch(
                requirement="Education Degree",
                is_required=False,
                candidate_evidence="Candidate Education Profile",
                match_status=MatchStatus.MATCH,
                match_type=MatchType.EDUCATION_MATCH,
                confidence=1.0,
                explanation="No specific degree level required by JD."
            )

        cand_degrees = [e.degree for e in resume_profile.education]
        if any("Bachelor" in d or "Master" in d or "Doctorate" in d for d in cand_degrees):
            return RequirementMatch(
                requirement=req_edu,
                is_required=True,
                candidate_evidence=", ".join(cand_degrees),
                match_status=MatchStatus.MATCH,
                match_type=MatchType.EDUCATION_MATCH,
                confidence=0.95,
                explanation=f"Candidate degree ({cand_degrees[0]}) satisfies education requirement."
            )

        return RequirementMatch(
            requirement=req_edu,
            is_required=True,
            candidate_evidence="NO_DEGREE_LISTED",
            match_status=MatchStatus.PARTIAL_MATCH,
            match_type=MatchType.EDUCATION_MATCH,
            confidence=0.60,
            explanation="Candidate profile does not explicitly state a relevant degree."
        )
