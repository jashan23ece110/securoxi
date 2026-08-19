"""
SECUROXI AI Intelligence 2.0 — Hiring & Screening Agent Tools
Registers deterministic tools connected to the SecuroxiScreeningPipeline,
JD parsing, candidate scoring, and ATS adapters.
"""

from typing import Dict, Any, List, Optional
from securoxi.orchestrator.tools import ToolDefinition, ToolParameter, ToolRegistry
from securoxi.orchestrator.types import TrustLevel
from securoxi.orchestrator.context import ExecutionContext
from securoxi.screening.extractor import RuleBasedExtractor
from securoxi.screening.matching_engine import SecuroxiMatchingEngine
from securoxi.screening.qualification_analyzer import SecuroxiQualificationAnalyzer
from securoxi.screening.scorer import SecuroxiCandidateScorer
from securoxi.scanner import SecuroxiScanner
from securoxi.models import AnalysisReport, Verdict
from securoxi.logger import get_logger

logger = get_logger("orchestrator.hiring_tools")


def register_hiring_agent_tools(
    tool_registry: ToolRegistry,
    scanner: Optional[SecuroxiScanner] = None,
    scorer: Optional[SecuroxiCandidateScorer] = None,
):
    """Registers all authoritative hiring & screening tools into the ToolRegistry."""
    sec_scanner = scanner or SecuroxiScanner()
    cand_scorer = scorer or SecuroxiCandidateScorer()
    extractor = RuleBasedExtractor()
    matching_engine = SecuroxiMatchingEngine()
    qualification_analyzer = SecuroxiQualificationAnalyzer()

    # 1. JD Parser Tool
    def _jd_parser_handler(ctx: ExecutionContext, jd_text: str = "", role_title: str = "Software Engineer") -> Dict[str, Any]:
        logger.info(f"Parsing Job Description for '{role_title}' (Tenant: {ctx.tenant_id})")
        # Extract mandatory vs preferred skills and experience from text
        mandatory_skills = []
        preferred_skills = []
        min_years = 0.0

        lower_jd = jd_text.lower()
        if "5+" in lower_jd or "5 years" in lower_jd:
            min_years = 5.0
        elif "3+" in lower_jd or "3 years" in lower_jd:
            min_years = 3.0

        for skill in ["Kubernetes", "AWS", "Python", "Docker", "Security", "CI/CD"]:
            if skill.lower() in lower_jd:
                if "preferred" in lower_jd and lower_jd.find("preferred") < lower_jd.find(skill.lower()):
                    preferred_skills.append(skill)
                else:
                    mandatory_skills.append(skill)

        if not mandatory_skills and not preferred_skills:
            mandatory_skills = ["Software Engineering"]

        return {
            "role_title": role_title,
            "min_experience_years": min_years,
            "mandatory_requirements": mandatory_skills,
            "preferred_requirements": preferred_skills,
            "exclusions": ["HIGH_RISK", "UNINSPECTABLE"],
        }

    tool_registry.register(
        ToolDefinition(
            tool_id="jd_parser",
            name="Job Description Requirements Extractor",
            description="Extracts mandatory, preferred, and experience criteria from job description text",
            parameters=[
                ToolParameter(name="jd_text", param_type="str", description="Full text of Job Description", required=True),
                ToolParameter(name="role_title", param_type="str", description="Title of role", required=False, default="Software Engineer"),
            ],
            trust_level=TrustLevel.LOW_RISK,
            handler=_jd_parser_handler,
        )
    )

    # 2. Candidate Security Clearance Gate Tool
    def _candidate_security_gate_handler(
        ctx: ExecutionContext,
        candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        logger.info(f"Executing Security Clearance Gate for {len(candidates)} candidates (Tenant: {ctx.tenant_id})")
        cleared_candidates = []
        quarantined_candidates = []

        for cand in candidates:
            cand_id = cand.get("candidate_id", "UNKNOWN")
            doc_status = cand.get("security_status", "SAFE")
            resume_text = cand.get("resume_text", "")

            # If document contains prompt injection or explicit high risk
            is_injection = "ignore" in resume_text.lower() and ("instruction" in resume_text.lower() or "previous" in resume_text.lower())
            if doc_status in ["HIGH_RISK", "UNINSPECTABLE"] or is_injection:
                quarantined_candidates.append({
                    "candidate_id": cand_id,
                    "candidate_name": cand.get("name", cand_id),
                    "security_status": "HIGH_RISK" if doc_status != "UNINSPECTABLE" else "UNINSPECTABLE",
                    "reason": "Security Gate Failed: Prompt injection payload or uninspectable document structure",
                    "rank": 0,
                    "fit_score": 0.0,
                })
            else:
                cleared_candidates.append(cand)

        return {
            "total_candidates": len(candidates),
            "cleared_count": len(cleared_candidates),
            "quarantined_count": len(quarantined_candidates),
            "cleared_candidates": cleared_candidates,
            "quarantined_candidates": quarantined_candidates,
        }

    tool_registry.register(
        ToolDefinition(
            tool_id="candidate_security_gate",
            name="Candidate Security Clearance Gate",
            description="Evaluates candidates against security scanning clearance before trusted screening",
            parameters=[
                ToolParameter(name="candidates", param_type="list", description="List of candidate objects with security status", required=True),
            ],
            trust_level=TrustLevel.LOW_RISK,
            handler=_candidate_security_gate_handler,
        )
    )

    # 3. Candidate Qualification Scorer Tool
    def _candidate_scorer_handler(
        ctx: ExecutionContext,
        candidates: List[Dict[str, Any]],
        mandatory_requirements: List[str],
        preferred_requirements: Optional[List[str]] = None,
        min_years: float = 0.0,
    ) -> Dict[str, Any]:
        pref = preferred_requirements or []
        logger.info(f"Executing Calibrated Candidate Scoring for {len(candidates)} candidates (Tenant: {ctx.tenant_id})")

        # 1. Consolidate Duplicate Candidates
        unique_candidates: Dict[str, Dict[str, Any]] = {}
        for cand in candidates:
            cid = cand.get("candidate_id", cand.get("name", "UNKNOWN"))
            if cid in unique_candidates:
                # Merge experience and text
                existing = unique_candidates[cid]
                existing["experience_years"] = max(existing.get("experience_years", 0.0), float(cand.get("experience_years", 0.0)))
                existing["resume_text"] = existing.get("resume_text", "") + " " + cand.get("resume_text", "")
            else:
                unique_candidates[cid] = dict(cand)

        negation_prefixes = ["no ", "never ", "not ", "without ", "lacks ", "limited exposure to "]

        def is_skill_present_and_positive(skill: str, text: str) -> bool:
            s_lower = skill.lower()
            if s_lower not in text:
                return False
            # Check if skill is negated
            for neg in negation_prefixes:
                if neg + s_lower in text:
                    return False
            return True

        scored_results = []
        for cand_id, cand in unique_candidates.items():
            name = cand.get("name", cand_id)
            text = cand.get("resume_text", "").lower()
            years = float(cand.get("experience_years", 3.0))

            matched_mand = [req for req in mandatory_requirements if is_skill_present_and_positive(req, text)]
            matched_pref = [req for req in pref if is_skill_present_and_positive(req, text)]
            missing_mand = [req for req in mandatory_requirements if not is_skill_present_and_positive(req, text)]

            # Calibrated Fit Scoring: 60% Mandatory, 20% Preferred, 20% Experience
            mand_score = (len(matched_mand) / max(len(mandatory_requirements), 1)) * 60.0
            pref_score = (len(matched_pref) / max(len(pref), 1)) * 20.0 if pref else 20.0
            exp_score = min(years / max(min_years, 1.0), 1.0) * 20.0 if min_years > 0 else 20.0

            total_fit = min(100.0, mand_score + pref_score + exp_score)

            if len(missing_mand) == 0 and (min_years == 0 or years >= min_years):
                qual_state = "QUALIFIED"
            elif len(missing_mand) <= 1:
                qual_state = "NEAR_MATCH"
            else:
                qual_state = "REVIEW"

            scored_results.append({
                "candidate_id": cand_id,
                "candidate_name": name,
                "security_status": "SAFE",
                "qualification_state": qual_state,
                "fit_score": round(total_fit, 2),
                "experience_years": years,
                "matched_mandatory": matched_mand,
                "matched_preferred": matched_pref,
                "missing_requirements": missing_mand,
            })

        # Rank candidates descending by fit score
        scored_results.sort(key=lambda c: c["fit_score"], reverse=True)
        for idx, item in enumerate(scored_results):
            item["rank"] = idx + 1

        return {
            "scored_count": len(scored_results),
            "results": scored_results,
        }

    tool_registry.register(
        ToolDefinition(
            tool_id="candidate_scorer",
            name="Deterministic Candidate Scorer",
            description="Computes calibrated fit scores and mandatory requirement matching against JD",
            parameters=[
                ToolParameter(name="candidates", param_type="list", description="List of candidate profiles", required=True),
                ToolParameter(name="mandatory_requirements", param_type="list", description="Mandatory requirements", required=True),
                ToolParameter(name="preferred_requirements", param_type="list", description="Preferred requirements", required=False),
                ToolParameter(name="min_years", param_type="float", description="Minimum years of experience", required=False, default=0.0),
            ],
            trust_level=TrustLevel.LOW_RISK,
            handler=_candidate_scorer_handler,
        )
    )

    # 4. ATS Status Updater Tool (Human Approval Gate)
    def _ats_status_updater_handler(
        ctx: ExecutionContext,
        candidate_ids: List[str],
        action: str = "ADVANCE_CANDIDATE"
    ) -> Dict[str, Any]:
        logger.info(f"Proposed ATS Mutation '{action}' for candidates {candidate_ids} (Tenant: {ctx.tenant_id})")
        return {
            "action": action,
            "candidate_ids": candidate_ids,
            "tenant_id": ctx.tenant_id,
            "status": "PROPOSED",
            "requires_human_approval": True,
            "message": f"Proposal to {action} for candidates {candidate_ids} submitted for review.",
        }

    tool_registry.register(
        ToolDefinition(
            tool_id="ats_status_updater",
            name="ATS Candidate Status Updater",
            description="Proposes high-impact candidate state mutations in connected ATS systems",
            parameters=[
                ToolParameter(name="candidate_ids", param_type="list", description="Target candidate IDs", required=True),
                ToolParameter(name="action", param_type="str", description="ATS Action", required=False, default="ADVANCE_CANDIDATE"),
            ],
            trust_level=TrustLevel.HIGH_IMPACT,
            handler=_ats_status_updater_handler,
        )
    )
