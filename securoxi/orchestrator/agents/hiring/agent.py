"""
SECUROXI AI Intelligence 2.0 — Specialized Hiring & Screening Agent
Coordinates JD analysis, candidate security clearance, deterministic scoring,
shortlist ranking, and human-in-the-loop ATS mutations.
"""

from typing import Dict, Any, List, Optional
from securoxi.orchestrator.agents.base import AbstractAgent
from securoxi.orchestrator.agents.models import (
    AgentDefinition,
    AgentDecision,
    AgentOutput,
)
from securoxi.orchestrator.agents.types import (
    AgentDomain,
    AgentCapability,
    AgentRiskLevel,
    AgentLifecycleState,
    AgentActionType,
)
from securoxi.orchestrator.agents.hiring.types import (
    CandidateQualificationState,
    RequirementType,
    EvidenceQualityTier,
    ATSOperationType,
)
from securoxi.orchestrator.agents.hiring.models import (
    RequirementCriterion,
    JDAnalysis,
    CandidateScreeningResult,
    HiringAgentResult,
)
from securoxi.orchestrator.types import TrustLevel
from securoxi.orchestrator.planning.types import TaskIntent
from securoxi.orchestrator.context import ExecutionContext
from securoxi.logger import get_logger

logger = get_logger("orchestrator.hiring_agent")


def get_default_hiring_agent_definition() -> AgentDefinition:
    """Returns the system-owned AgentDefinition for the specialized Hiring Agent."""
    return AgentDefinition(
        agent_id="hiring-agent",
        name="Securoxi Autonomous Hiring & Screening Agent",
        description="Evaluates candidate pools against JDs, enforces security gates, executes deterministic scoring, and generates shortlists",
        version="1.0.0",
        domain=AgentDomain.HIRING,
        capabilities=[
            AgentCapability.CANDIDATE_SCREENING,
            AgentCapability.JD_MATCHING,
            AgentCapability.REPORT_GENERATION,
        ],
        trust_level=TrustLevel.CONTROLLED,
        risk_level=AgentRiskLevel.MEDIUM,
        allowed_tools={
            "jd_parser",
            "candidate_security_gate",
            "candidate_scorer",
            "ats_status_updater",
        },
        supported_intents=[
            TaskIntent.CANDIDATE_SCREENING,
            TaskIntent.JD_MATCHING,
            TaskIntent.ATS_OPERATION,
            TaskIntent.DOCUMENT_ANALYSIS,
            TaskIntent.QUESTION_ANSWERING,
            TaskIntent.MIXED_WORKFLOW,
        ],
        max_iterations=12,
        enabled=True,
    )


class HiringAgent(AbstractAgent):
    """
    Autonomous Hiring & Candidate Screening Agent.
    Enforces security-first clearance before candidate evaluation, computes calibrated
    fit scores, and compiles auditable shortlists.
    """

    def __init__(self, definition: Optional[AgentDefinition] = None):
        agent_def = definition or get_default_hiring_agent_definition()
        super().__init__(definition=agent_def)

        self.jd_analysis: Optional[JDAnalysis] = None
        self.raw_candidates: List[Dict[str, Any]] = []
        self.cleared_candidates: List[Dict[str, Any]] = []
        self.quarantined_candidates: List[Dict[str, Any]] = []
        self.candidate_results: List[CandidateScreeningResult] = []
        self.approval_requirements: List[Dict[str, Any]] = []
        self._step = 0

    def initialize(self, context: ExecutionContext, **kwargs) -> bool:
        super().initialize(context, **kwargs)
        self.jd_analysis = None
        self.raw_candidates = []
        self.cleared_candidates = []
        self.quarantined_candidates = []
        self.candidate_results = []
        self.approval_requirements = []
        self._step = 0
        return True

    def decide(self, context: ExecutionContext) -> AgentDecision:
        """
        Screening & Triage Decision Loop:
        1. Extract and normalize Job Description requirements.
        2. Execute Candidate Security Clearance Gate.
        3. Score cleared candidates against mandatory/preferred criteria.
        4. Propose ATS state mutation (if requested).
        5. Finalize Shortlist and explain top candidates.
        """
        self._process_latest_observations()

        params = self._get_initial_parameters()
        jd_text = params.get("jd_text", "Software Engineer with 5+ years experience and Kubernetes")
        candidates = params.get("candidates", [])
        self.raw_candidates = candidates

        # Step 1: Parse Job Description
        if not self.jd_analysis:
            return AgentDecision(
                decision_type=AgentActionType.USE_TOOL,
                target_tool_id="jd_parser",
                tool_arguments={"jd_text": jd_text, "role_title": params.get("role_title", "Software Engineer")},
                reasoning_summary="Extracting mandatory and preferred criteria from Job Description",
            )

        # Step 2: Apply Security Clearance Gate
        if not self.cleared_candidates and not self.quarantined_candidates and self.raw_candidates:
            return AgentDecision(
                decision_type=AgentActionType.USE_TOOL,
                target_tool_id="candidate_security_gate",
                tool_arguments={"candidates": self.raw_candidates},
                reasoning_summary="Applying mandatory Security Clearance Gate before candidate screening",
            )

        # Step 3: Candidate Qualification Scoring
        if not self.candidate_results and self.cleared_candidates:
            mand_reqs = [r.name for r in self.jd_analysis.mandatory_requirements]
            pref_reqs = [r.name for r in self.jd_analysis.preferred_requirements]
            min_yrs = self.jd_analysis.mandatory_requirements[0].min_years if self.jd_analysis.mandatory_requirements else 0.0

            return AgentDecision(
                decision_type=AgentActionType.USE_TOOL,
                target_tool_id="candidate_scorer",
                tool_arguments={
                    "candidates": self.cleared_candidates,
                    "mandatory_requirements": mand_reqs,
                    "preferred_requirements": pref_reqs,
                    "min_years": min_yrs,
                },
                reasoning_summary="Computing calibrated fit scores and mandatory matching for cleared candidates",
            )

        # Step 4: Check if ATS write action requested
        ats_action = params.get("ats_action")
        if ats_action and not self.approval_requirements and self.candidate_results:
            top_ids = [c.candidate_id for c in self.candidate_results if c.qualification_state == CandidateQualificationState.QUALIFIED]
            return AgentDecision(
                decision_type=AgentActionType.USE_TOOL,
                target_tool_id="ats_status_updater",
                tool_arguments={"candidate_ids": top_ids, "action": ats_action},
                reasoning_summary=f"Proposing ATS mutation '{ats_action}' for qualified candidates",
            )

        # Step 5: Finish Screening Task
        return AgentDecision(
            decision_type=AgentActionType.FINISH,
            reasoning_summary=f"Screening complete. Evaluated {len(self.candidate_results)} cleared candidates. {len(self.quarantined_candidates)} quarantined.",
            confidence=0.95,
        )

    def finalize(self, context: ExecutionContext) -> AgentOutput:
        """Constructs the strongly typed AgentOutput with HiringAgentResult."""
        params = self._get_initial_parameters()
        top_n = params.get("top_n", 10)

        # Add quarantined candidates at Rank #0 with 0 fit score
        all_results = list(self.candidate_results)
        for q in self.quarantined_candidates:
            all_results.append(
                CandidateScreeningResult(
                    candidate_id=q["candidate_id"],
                    candidate_name=q["candidate_name"],
                    security_status=q["security_status"],
                    qualification_state=CandidateQualificationState.QUARANTINED if q["security_status"] == "HIGH_RISK" else CandidateQualificationState.UNINSPECTABLE,
                    fit_score=0.0,
                    rank=0,
                    warnings=[q.get("reason", "Quarantined by Security Gate")],
                    explanation=f"Candidate document quarantined: {q.get('reason', 'Security Block')}",
                )
            )

        qualified = [c.candidate_id for c in self.candidate_results if c.qualification_state == CandidateQualificationState.QUALIFIED]
        near_matches = [c.candidate_id for c in self.candidate_results if c.qualification_state == CandidateQualificationState.NEAR_MATCH]
        quarantined = [q["candidate_id"] for q in self.quarantined_candidates]
        shortlist = qualified[:top_n]

        hiring_result = HiringAgentResult(
            task_summary=f"Screened {len(self.raw_candidates)} candidate documents for '{self.jd_analysis.title if self.jd_analysis else 'Role'}'.",
            job_context=self.jd_analysis.to_dict() if self.jd_analysis else {},
            security_summary={
                "total_screened": len(self.raw_candidates),
                "cleared": len(self.cleared_candidates),
                "quarantined": len(self.quarantined_candidates),
            },
            candidate_results=all_results,
            qualified_candidates=qualified,
            near_matches=near_matches,
            quarantined_candidates=quarantined,
            shortlist=shortlist,
            approval_requirements=self.approval_requirements,
            total_discovered=len(self.raw_candidates),
            total_evaluated=len(self.cleared_candidates),
            is_partial_coverage=False,
            coverage_percentage=100.0,
        )

        self.state = AgentLifecycleState.COMPLETED
        return AgentOutput(
            agent_id=self.agent_id,
            version=self.version,
            status=self.state,
            result_data=hiring_result.to_dict(),
            evidence_references=[f"Candidate:{c.candidate_id}" for c in all_results],
            provenance=[f"Tenant:{context.tenant_id}", f"Agent:{self.agent_id}", f"Shortlist:{len(shortlist)}"],
            recommended_next_steps=["REVIEW_SHORTLIST", "PROCEED_TO_INTERVIEWS"],
            warnings=[f"Quarantined {len(quarantined)} candidates at Rank #0"] if quarantined else [],
            confidence=0.95,
        )

    def _process_latest_observations(self):
        """Processes tool output observations and updates agent state."""
        for obs in self._observations:
            if obs.source == "TOOL_RESULT" and isinstance(obs.payload, dict):
                # 1. JD Parser Result
                if "mandatory_requirements" in obs.payload and not self.jd_analysis:
                    mand = [RequirementCriterion(req_id=f"MAND-{i+1}", name=m, min_years=obs.payload.get("min_experience_years", 0.0)) for i, m in enumerate(obs.payload.get("mandatory_requirements", []))]
                    pref = [RequirementCriterion(req_id=f"PREF-{i+1}", name=p, req_type=RequirementType.PREFERRED) for i, p in enumerate(obs.payload.get("preferred_requirements", []))]
                    self.jd_analysis = JDAnalysis(
                        title=obs.payload.get("role_title", "Software Engineer"),
                        mandatory_requirements=mand,
                        preferred_requirements=pref,
                        exclusions=obs.payload.get("exclusions", []),
                    )

                # 2. Security Clearance Gate Result
                if "cleared_candidates" in obs.payload and not self.cleared_candidates:
                    self.cleared_candidates = obs.payload.get("cleared_candidates", [])
                    self.quarantined_candidates = obs.payload.get("quarantined_candidates", [])

                # 3. Scorer Result
                if "results" in obs.payload and not self.candidate_results:
                    for item in obs.payload.get("results", []):
                        state_val = CandidateQualificationState(item.get("qualification_state", "QUALIFIED"))
                        self.candidate_results.append(
                            CandidateScreeningResult(
                                candidate_id=item.get("candidate_id", ""),
                                candidate_name=item.get("candidate_name", ""),
                                security_status=item.get("security_status", "SAFE"),
                                qualification_state=state_val,
                                fit_score=float(item.get("fit_score", 0.0)),
                                matched_mandatory=item.get("matched_mandatory", []),
                                matched_preferred=item.get("matched_preferred", []),
                                missing_requirements=item.get("missing_requirements", []),
                                rank=int(item.get("rank", 1)),
                                explanation=f"Candidate matched {len(item.get('matched_mandatory', []))} mandatory requirements with fit score {item.get('fit_score', 0.0)}.",
                            )
                        )

                # 4. ATS Status Updater Result
                if "requires_human_approval" in obs.payload:
                    self.approval_requirements.append(obs.payload)

    def _get_initial_parameters(self) -> Dict[str, Any]:
        """Extracts input parameters from initial observation."""
        for obs in self._observations:
            if obs.source == "AGENT_INPUT" and isinstance(obs.payload, dict):
                return obs.payload
        return {}
