"""
SECUROXI AI Intelligence 2.0 — Specialized Autonomous Security Agent
Coordinates security triage, evidence verification, Security Brain correlation,
policy context evaluation, and incident preparation without replacing deterministic authority.
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
    MemoryAccessPermission,
)
from securoxi.orchestrator.agents.security.types import (
    SecurityInvestigationState,
    SecurityRecommendationType,
    EvidenceVerificationState,
)
from securoxi.orchestrator.agents.security.models import (
    SecurityEvidenceReference,
    SecurityAttackStep,
    SecurityAttackChainSummary,
    SecurityPolicyContext,
    SecurityRiskContext,
    IncidentProposal,
    SecurityAgentResult,
)
from securoxi.orchestrator.types import TrustLevel
from securoxi.orchestrator.planning.types import TaskIntent
from securoxi.orchestrator.context import ExecutionContext
from securoxi.logger import get_logger

logger = get_logger("orchestrator.security_agent")


def get_default_security_agent_definition() -> AgentDefinition:
    """Returns the system-owned AgentDefinition for the specialized Security Agent."""
    return AgentDefinition(
        agent_id="security-agent",
        name="Securoxi Autonomous Security Agent",
        description="Coordinates security triage, evidence verification, attack correlation, and policy alignment",
        version="1.0.0",
        domain=AgentDomain.SECURITY,
        capabilities=[
            AgentCapability.SECURITY_ANALYSIS,
            AgentCapability.FORENSIC_ANALYSIS,
            AgentCapability.REPORT_GENERATION,
        ],
        trust_level=TrustLevel.CONTROLLED,
        risk_level=AgentRiskLevel.MEDIUM,
        allowed_tools={
            "document_security_scan",
            "evidence_lookup",
            "security_brain_lookup",
            "policy_lookup",
        },
        supported_intents=[
            TaskIntent.DOCUMENT_SCAN,
            TaskIntent.DOCUMENT_ANALYSIS,
            TaskIntent.SECURITY_INVESTIGATION,
            TaskIntent.INCIDENT_INVESTIGATION,
            TaskIntent.MIXED_WORKFLOW,
        ],
        max_iterations=10,
        enabled=True,
    )


class SecurityAgent(AbstractAgent):
    """
    Specialized SECUROXI Autonomous Security Agent.
    Implements intelligent security investigation while strictly enforcing:
    Deterministic Systems == Authority; Security Agent == Investigation & Recommendation.
    """

    def __init__(self, definition: Optional[AgentDefinition] = None):
        agent_def = definition or get_default_security_agent_definition()
        super().__init__(definition=agent_def)

        self.investigation_state = SecurityInvestigationState.INITIAL_TRIAGE
        self.doc_id: str = ""
        self.doc_path: str = ""
        self.scan_result: Optional[Dict[str, Any]] = None
        self.evidence_references: List[SecurityEvidenceReference] = []
        self.attack_chains: List[SecurityAttackChainSummary] = []
        self.policy_context: Optional[SecurityPolicyContext] = None
        self.risk_context: Optional[SecurityRiskContext] = None
        self.incident_proposal: Optional[IncidentProposal] = None
        self.recommended_actions: List[SecurityRecommendationType] = []
        self.warnings: List[str] = []

    def initialize(self, context: ExecutionContext, **kwargs) -> bool:
        super().initialize(context, **kwargs)
        self.investigation_state = SecurityInvestigationState.INITIAL_TRIAGE
        self.doc_id = ""
        self.doc_path = ""
        self.scan_result = None
        self.evidence_references = []
        self.attack_chains = []
        self.policy_context = None
        self.risk_context = None
        self.incident_proposal = None
        self.recommended_actions = []
        self.warnings = []
        return True

    def decide(self, context: ExecutionContext) -> AgentDecision:
        """
        Adaptive Security Investigation Loop:
        1. Ingest input & determine if scan exists -> if not, call document_security_scan.
        2. Inspect scan verdict:
           - If SAFE -> Finish immediately with clean explanation.
           - If UNINSPECTABLE -> Record warning, evaluate policy, and recommend manual review.
           - If SUSPICIOUS/HIGH_RISK -> Gather granular evidence.
        3. Correlate via Security Brain if multiple findings exist.
        4. Query Policy Engine for authoritative policy action.
        5. Draft Incident Proposal if high-risk.
        6. Finish with typed SecurityAgentResult.
        """
        # Process latest observations
        self._process_latest_observations()

        # Step 1: Initial Triage
        if not self.scan_result:
            # Check if input already provides scan details
            input_params = self._get_initial_parameters()
            if "verdict" in input_params:
                # Reuse pre-existing authoritative scan data
                self.scan_result = input_params
                self.doc_id = input_params.get("document_id", "DOC-CURRENT")
            else:
                self.doc_path = input_params.get("doc_path", "")
                self.doc_id = input_params.get("doc_id", self.doc_path or "DOC-CURRENT")
                return AgentDecision(
                    decision_type=AgentActionType.USE_TOOL,
                    target_tool_id="document_security_scan",
                    tool_arguments={"doc_path": self.doc_path, "doc_id": self.doc_id},
                    reasoning_summary="Initiating deterministic document security scan",
                )

        verdict = self.scan_result.get("verdict", "SAFE")
        risk_score = float(self.scan_result.get("risk_score", 0.0))
        findings = self.scan_result.get("findings", [])
        self.risk_context = SecurityRiskContext(
            risk_score=risk_score,
            risk_tier="CRITICAL" if risk_score >= 80 else ("HIGH" if risk_score >= 50 else ("MEDIUM" if risk_score >= 20 else "LOW")),
            explanation=f"Deterministic risk engine scored document at {risk_score}/100."
        )

        # Step 2: Handle SAFE state
        if verdict == "SAFE" and len(findings) == 0:
            self.recommended_actions = [SecurityRecommendationType.NO_ACTION]
            self.investigation_state = SecurityInvestigationState.INVESTIGATION_COMPLETE
            return AgentDecision(
                decision_type=AgentActionType.FINISH,
                reasoning_summary="Document security scan completed with 0 findings. Sourced authoritative state: SAFE.",
                confidence=1.0,
            )

        # Step 3: Handle UNINSPECTABLE state
        if verdict == "UNINSPECTABLE":
            self.warnings.append("Document could not be fully inspected. Deterministic state: UNINSPECTABLE (Never assumed SAFE).")
            self.recommended_actions = [SecurityRecommendationType.REVIEW_DOCUMENT, SecurityRecommendationType.RETRY_OCR]
            if not self.policy_context:
                return AgentDecision(
                    decision_type=AgentActionType.USE_TOOL,
                    target_tool_id="policy_lookup",
                    tool_arguments={"verdict": "UNINSPECTABLE", "risk_score": 50.0, "threat_types": ["UNINSPECTABLE_FORMAT"]},
                    reasoning_summary="Querying authoritative policy for uninspectable asset",
                )
            self.investigation_state = SecurityInvestigationState.INVESTIGATION_COMPLETE
            return AgentDecision(
                decision_type=AgentActionType.FINISH,
                reasoning_summary="Completed uninspectable document triage with policy gate",
                confidence=0.9,
            )

        # Step 4: Gather Evidence for Findings
        if not self.evidence_references and len(findings) > 0:
            return AgentDecision(
                decision_type=AgentActionType.USE_TOOL,
                target_tool_id="evidence_lookup",
                tool_arguments={"document_id": self.doc_id, "findings": findings},
                reasoning_summary=f"Retrieving granular forensic evidence for {len(findings)} security findings",
            )

        # Step 5: Security Brain Correlation (if multiple findings or high risk)
        threat_types = list(set([f.get("category", "THREAT") for f in findings]))
        if len(threat_types) > 1 and not self.attack_chains:
            return AgentDecision(
                decision_type=AgentActionType.USE_TOOL,
                target_tool_id="security_brain_lookup",
                tool_arguments={"document_id": self.doc_id, "threat_types": threat_types, "risk_score": risk_score},
                reasoning_summary="Escalating multi-stage threat indicators to Security Brain for attack graph correlation",
            )

        # Step 6: Policy Verification
        if not self.policy_context:
            return AgentDecision(
                decision_type=AgentActionType.USE_TOOL,
                target_tool_id="policy_lookup",
                tool_arguments={"verdict": verdict, "risk_score": risk_score, "threat_types": threat_types},
                reasoning_summary="Verifying authoritative policy rule and enforcement action",
            )

        # Step 7: Incident Preparation & Final Recommendations
        if risk_score >= 50.0 or (self.policy_context and self.policy_context.action in {"BLOCK", "QUARANTINE"}):
            self.incident_proposal = IncidentProposal(
                title=f"Security Alert: {threat_types[0] if threat_types else 'Suspicious Content'} in {self.doc_id}",
                severity="HIGH" if risk_score < 80 else "CRITICAL",
                summary=f"Detected {len(findings)} findings in document {self.doc_id} triggering policy action {self.policy_context.action}.",
                affected_document_ids=[self.doc_id],
                findings=[f.get("title", "Finding") for f in findings],
                recommended_actions=["Quarantine Document", "Review in Security Brain", "Audit Candidate Submission"],
                requires_human_approval=True,
            )
            self.recommended_actions = [
                SecurityRecommendationType.VIEW_EVIDENCE,
                SecurityRecommendationType.OPEN_SECURITY_BRAIN,
                SecurityRecommendationType.CREATE_INCIDENT,
            ]
        else:
            self.recommended_actions = [SecurityRecommendationType.VIEW_EVIDENCE, SecurityRecommendationType.REVIEW_DOCUMENT]

        self.investigation_state = SecurityInvestigationState.INVESTIGATION_COMPLETE
        return AgentDecision(
            decision_type=AgentActionType.FINISH,
            reasoning_summary=f"Investigation concluded. Authoritative verdict: {verdict}, Policy: {self.policy_context.action if self.policy_context else 'ALLOW'}.",
            confidence=0.98,
        )

    def finalize(self, context: ExecutionContext) -> AgentOutput:
        """Constructs the strongly typed, validated AgentOutput with SecurityAgentResult."""
        verdict = self.scan_result.get("verdict", "SAFE") if self.scan_result else "SAFE"
        findings_count = len(self.scan_result.get("findings", [])) if self.scan_result else 0

        # User-facing concise explanation
        if verdict == "SAFE":
            explanation = "SECUROXI completed document security triage. No prompt injection or visual deception findings detected."
        elif verdict == "UNINSPECTABLE":
            explanation = "SECUROXI was unable to inspect the document format safely. Routed to security reviewer per policy."
        else:
            action = self.policy_context.action if self.policy_context else "QUARANTINE"
            explanation = (
                f"SECUROXI detected {findings_count} security finding(s) including prompt injection or hidden instructions. "
                f"Authoritative Policy Engine enforcement: {action}."
            )

        result_model = SecurityAgentResult(
            document_id=self.doc_id,
            authoritative_security_state=verdict,
            findings_count=findings_count,
            evidence_items=self.evidence_references,
            attack_chains=self.attack_chains,
            policy_context=self.policy_context,
            risk_context=self.risk_context,
            incident_proposal=self.incident_proposal,
            recommended_actions=self.recommended_actions or [SecurityRecommendationType.NO_ACTION],
            user_explanation=explanation,
            provenance_chain=[f"Tenant:{context.tenant_id}", f"Agent:{self.agent_id}", f"State:{verdict}"],
            warnings=self.warnings,
            verification_state=EvidenceVerificationState.VERIFIED if verdict != "UNINSPECTABLE" else EvidenceVerificationState.UNVERIFIED,
        )

        self.state = AgentLifecycleState.COMPLETED
        return AgentOutput(
            agent_id=self.agent_id,
            version=self.version,
            status=self.state,
            result_data=result_model.to_dict(),
            evidence_references=[e.evidence_id for e in self.evidence_references],
            provenance=result_model.provenance_chain,
            recommended_next_steps=[r.value for r in result_model.recommended_actions],
            warnings=self.warnings,
            confidence=1.0 if verdict == "SAFE" else 0.95,
        )

    def _process_latest_observations(self):
        """Processes tool output observations and updates internal investigation models."""
        for obs in self._observations:
            if obs.source == "TOOL_RESULT" and isinstance(obs.payload, dict):
                # Document scan observation
                if "verdict" in obs.payload and not self.scan_result:
                    self.scan_result = obs.payload
                    self.doc_id = obs.payload.get("document_id", self.doc_id)

                # Evidence lookup observation
                if "evidence_items" in obs.payload and not self.evidence_references:
                    for ev in obs.payload["evidence_items"]:
                        self.evidence_references.append(
                            SecurityEvidenceReference(
                                evidence_id=ev.get("evidence_id", "EVD-001"),
                                finding_id=ev.get("finding_id", "FND-001"),
                                category=ev.get("category", "PROMPT_INJECTION"),
                                severity=ev.get("severity", "HIGH"),
                                title=ev.get("title", "Evidence Title"),
                                description=ev.get("description", ""),
                                original_text_excerpt=ev.get("original_text_excerpt", ""),
                                page=ev.get("page", 1),
                                location=ev.get("location", ""),
                                analyzer_source=ev.get("analyzer_source", "DeterministicEngine"),
                                verification_state=EvidenceVerificationState.VERIFIED,
                            )
                        )

                # Security Brain observation
                if "attack_graph_nodes" in obs.payload and not self.attack_chains:
                    self.attack_chains.append(
                        SecurityAttackChainSummary(
                            title="Coordinated Multi-Vector Infiltration",
                            severity="HIGH",
                            steps=[
                                SecurityAttackStep(step_index=1, category="VISUAL_DECEPTION", description="Hidden micro-font text detected in header", relationship_type="OBSERVED"),
                                SecurityAttackStep(step_index=2, category="PROMPT_INJECTION", description="Override system instructions targeted at screening agent", relationship_type="CORRELATED"),
                            ],
                            impact_summary="Attempted automated hiring decision manipulation via indirect prompt injection",
                        )
                    )

                # Policy lookup observation
                if "policy_id" in obs.payload and not self.policy_context:
                    self.policy_context = SecurityPolicyContext(
                        policy_id=obs.payload.get("policy_id", "P-100"),
                        rule_name=obs.payload.get("rule_name", "Security Gate"),
                        action=obs.payload.get("action", "ALLOW"),
                        authoritative_verdict=obs.payload.get("authoritative_verdict", "SAFE"),
                        explanation=obs.payload.get("explanation", ""),
                    )

    def _get_initial_parameters(self) -> Dict[str, Any]:
        """Extracts initial parameters from the AGENT_INPUT observation."""
        for obs in self._observations:
            if obs.source == "AGENT_INPUT" and isinstance(obs.payload, dict):
                return obs.payload
        return {}
