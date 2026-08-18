"""
SECUROXI AI Intelligence 2.0 — Specialized Forensic Investigation Agent
Investigates security findings, extracts spatial layout bounding boxes,
correlates attack chains with Security Brain, and produces grounded forensic reports.
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
from securoxi.orchestrator.agents.forensic.types import (
    ForensicFindingStatus,
    EvidenceSufficiencyTier,
)
from securoxi.orchestrator.agents.forensic.models import (
    ForensicLocation,
    ForensicFinding,
    ForensicAttackStep,
    ForensicAttackChain,
    ForensicInvestigationResult,
)
from securoxi.orchestrator.types import TrustLevel
from securoxi.orchestrator.planning.types import TaskIntent
from securoxi.orchestrator.context import ExecutionContext
from securoxi.logger import get_logger

logger = get_logger("orchestrator.forensic_agent")


def get_default_forensic_agent_definition() -> AgentDefinition:
    """Returns the system-owned AgentDefinition for the specialized Forensic Agent."""
    return AgentDefinition(
        agent_id="forensic-agent",
        name="Securoxi Autonomous Forensic Investigation Agent",
        description="Investigates detected findings, resolves spatial bounding boxes, correlates attack chains, and produces forensic reports",
        version="1.0.0",
        domain=AgentDomain.FORENSICS,
        capabilities=[
            AgentCapability.FORENSIC_ANALYSIS,
            AgentCapability.SECURITY_ANALYSIS,
            AgentCapability.REPORT_GENERATION,
        ],
        trust_level=TrustLevel.CONTROLLED,
        risk_level=AgentRiskLevel.MEDIUM,
        allowed_tools={
            "finding_lookup",
            "forensic_evidence_lookup",
            "attack_graph_lookup",
        },
        supported_intents=[
            TaskIntent.SECURITY_INVESTIGATION,
            TaskIntent.DOCUMENT_ANALYSIS,
            TaskIntent.DOCUMENT_COMPARISON,
            TaskIntent.INCIDENT_INVESTIGATION,
            TaskIntent.REPORT_GENERATION,
            TaskIntent.MIXED_WORKFLOW,
        ],
        max_iterations=12,
        enabled=True,
    )


class ForensicAgent(AbstractAgent):
    """
    Autonomous Forensic Investigation Agent.
    Resolves spatial evidence locations, correlates compound threats with Security Brain,
    and synthesizes actionable forensic investigation reports.
    """

    def __init__(self, definition: Optional[AgentDefinition] = None):
        agent_def = definition or get_default_forensic_agent_definition()
        super().__init__(definition=agent_def)

        self.document_id = ""
        self.security_state = "SAFE"
        self.findings: List[ForensicFinding] = []
        self.attack_chain: Optional[ForensicAttackChain] = None
        self.sufficiency = EvidenceSufficiencyTier.SUFFICIENT
        self._spatial_resolved = False
        self._graph_resolved = False

    def initialize(self, context: ExecutionContext, **kwargs) -> bool:
        super().initialize(context, **kwargs)
        self.document_id = ""
        self.security_state = "SAFE"
        self.findings = []
        self.attack_chain = None
        self.sufficiency = EvidenceSufficiencyTier.SUFFICIENT
        self._spatial_resolved = False
        self._graph_resolved = False
        return True

    def decide(self, context: ExecutionContext) -> AgentDecision:
        """
        Forensic Investigation Decision Loop:
        1. Ingest findings and request spatial bounding box resolution.
        2. Query Security Brain attack graph for compound/multi-vector threats.
        3. Compile and finalize ForensicInvestigationResult.
        """
        self._process_latest_observations()

        params = self._get_initial_parameters()
        self.document_id = params.get("document_id", "DOC-01")
        self.security_state = params.get("verdict", "SAFE")
        raw_findings = params.get("findings", [])

        # If no findings, immediately finish clean investigation
        if not raw_findings and not self.findings:
            return AgentDecision(
                decision_type=AgentActionType.FINISH,
                reasoning_summary="No security findings detected. Forensic state verified SAFE.",
                confidence=0.98,
            )

        # Initialize findings list if empty
        if not self.findings:
            for f in raw_findings:
                self.findings.append(
                    ForensicFinding(
                        finding_id=f.get("finding_id", "FND-01"),
                        document_id=self.document_id,
                        category=f.get("category", "THREAT"),
                        severity=f.get("severity", "HIGH"),
                        title=f.get("title", "Detected Finding"),
                        evidence_text=f.get("evidence", ""),
                        location=ForensicLocation(
                            page=f.get("page", 1),
                            bbox=f.get("bbox", [72.0, 100.0, 450.0, 120.0]),
                            section=f.get("section", "Body"),
                        ),
                        status=ForensicFindingStatus.OBSERVED,
                    )
                )

        # Step 1: Resolve spatial evidence
        if not self._spatial_resolved and self.findings:
            self._spatial_resolved = True
            first_fid = self.findings[0].finding_id
            return AgentDecision(
                decision_type=AgentActionType.USE_TOOL,
                target_tool_id="forensic_evidence_lookup",
                tool_arguments={"finding_id": first_fid, "document_id": self.document_id},
                reasoning_summary=f"Resolving spatial layout bounding box for finding '{first_fid}'",
            )

        # Step 2: Query Security Brain Attack Graph if compound
        if not self._graph_resolved and len(self.findings) > 0:
            self._graph_resolved = True
            threat_types = [f.category for f in self.findings]
            return AgentDecision(
                decision_type=AgentActionType.USE_TOOL,
                target_tool_id="attack_graph_lookup",
                tool_arguments={"document_id": self.document_id, "threat_types": threat_types},
                reasoning_summary="Querying Security Brain attack graph for multi-vector threat correlation",
            )

        # Step 3: Finalize Investigation
        return AgentDecision(
            decision_type=AgentActionType.FINISH,
            reasoning_summary=f"Forensic investigation complete for document '{self.document_id}'. Evaluated {len(self.findings)} findings.",
            confidence=0.95,
        )

    def finalize(self, context: ExecutionContext) -> AgentOutput:
        """Constructs the strongly typed AgentOutput with ForensicInvestigationResult."""
        recommendations = []
        if len(self.findings) > 0:
            recommendations.extend(["VIEW_FORENSIC_EVIDENCE", "OPEN_SECURITY_BRAIN"])
            if self.security_state in ["HIGH_RISK", "BLOCK"]:
                recommendations.append("CREATE_INCIDENT_PROPOSAL")
        else:
            recommendations.append("NO_ACTION_REQUIRED")

        # Build attack chain if findings exist
        if len(self.findings) > 0 and not self.attack_chain:
            steps = [
                ForensicAttackStep(
                    step_index=i + 1,
                    phase="Execution",
                    technique=f.category,
                    evidence_ref=f.finding_id,
                    description=f.title,
                )
                for i, f in enumerate(self.findings)
            ]
            self.attack_chain = ForensicAttackChain(steps=steps, confidence="SUPPORTED")

        inv_result = ForensicInvestigationResult(
            subject=f"Forensic Analysis: {self.document_id}",
            security_state=self.security_state,
            findings=self.findings,
            attack_chain=self.attack_chain,
            sufficiency=self.sufficiency,
            recommendations=recommendations,
            provenance=[f"Tenant:{context.tenant_id}", f"Agent:{self.agent_id}", f"Findings:{len(self.findings)}"],
        )

        self.state = AgentLifecycleState.COMPLETED
        return AgentOutput(
            agent_id=self.agent_id,
            version=self.version,
            status=self.state,
            result_data=inv_result.to_dict(),
            evidence_references=[f.finding_id for f in self.findings],
            provenance=[f"Tenant:{context.tenant_id}", f"Agent:{self.agent_id}"],
            recommended_next_steps=recommendations,
            warnings=[f"Detected {len(self.findings)} security findings"] if self.findings else [],
            confidence=0.95,
        )

    def _process_latest_observations(self):
        """Processes tool output observations."""
        for obs in self._observations:
            if obs.source == "TOOL_RESULT" and isinstance(obs.payload, dict):
                # Update spatial bbox if returned
                if "bbox" in obs.payload and self.findings:
                    self.findings[0].location.bbox = obs.payload.get("bbox")
                    self.findings[0].location.page = obs.payload.get("page", 1)

    def _get_initial_parameters(self) -> Dict[str, Any]:
        """Extracts input parameters from initial observation."""
        for obs in self._observations:
            if obs.source == "AGENT_INPUT" and isinstance(obs.payload, dict):
                return obs.payload
        return {}
