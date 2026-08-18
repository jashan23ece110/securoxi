"""
SECUROXI AI Intelligence 2.0 — Specialized Incident Response Agent
Coordinates incident triage, timeline synthesis, entity correlation,
and human-in-the-loop response action proposals.
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
from securoxi.orchestrator.agents.incident.types import (
    IncidentTriageSeverity,
    IncidentRecommendationType,
)
from securoxi.orchestrator.agents.incident.models import (
    IncidentTimelineEvent,
    IncidentCorrelationItem,
    IncidentProposal,
    IncidentAgentResult,
)
from securoxi.orchestrator.types import TrustLevel
from securoxi.orchestrator.planning.types import TaskIntent
from securoxi.orchestrator.context import ExecutionContext
from securoxi.logger import get_logger

logger = get_logger("orchestrator.incident_agent")


def get_default_incident_agent_definition() -> AgentDefinition:
    """Returns the system-owned AgentDefinition for the specialized Incident Agent."""
    return AgentDefinition(
        agent_id="incident-agent",
        name="Securoxi Autonomous Incident Response Agent",
        description="Triages incidents, builds event timelines, correlates affected assets, and prepares response proposals",
        version="1.0.0",
        domain=AgentDomain.INCIDENTS,
        capabilities=[
            AgentCapability.INCIDENT_INVESTIGATION,
            AgentCapability.FORENSIC_ANALYSIS,
            AgentCapability.REPORT_GENERATION,
        ],
        trust_level=TrustLevel.HIGH_IMPACT,
        risk_level=AgentRiskLevel.HIGH,
        allowed_tools={
            "incident_lookup",
            "incident_timeline_builder",
            "incident_response_proposer",
        },
        supported_intents=[
            TaskIntent.INCIDENT_INVESTIGATION,
            TaskIntent.SECURITY_INVESTIGATION,
            TaskIntent.MIXED_WORKFLOW,
            TaskIntent.REPORT_GENERATION,
        ],
        max_iterations=12,
        enabled=True,
    )


class IncidentAgent(AbstractAgent):
    """
    Autonomous Incident Response Agent.
    Triages security incidents, extracts chronological audit timelines,
    and drafts controlled response proposals requiring human-in-the-loop approval.
    """

    def __init__(self, definition: Optional[AgentDefinition] = None):
        agent_def = definition or get_default_incident_agent_definition()
        super().__init__(definition=agent_def)

        self.incident_id = ""
        self.lifecycle_state = "TRIAGED"
        self.severity = "HIGH"
        self.affected_asset = "UNKNOWN"
        self.timeline: List[IncidentTimelineEvent] = []
        self.correlations: List[IncidentCorrelationItem] = []
        self.proposals: List[IncidentProposal] = []
        self._lookup_done = False
        self._timeline_built = False
        self._response_proposed = False

    def initialize(self, context: ExecutionContext, **kwargs) -> bool:
        super().initialize(context, **kwargs)
        self.incident_id = ""
        self.lifecycle_state = "TRIAGED"
        self.severity = "HIGH"
        self.affected_asset = "UNKNOWN"
        self.timeline = []
        self.correlations = []
        self.proposals = []
        self._lookup_done = False
        self._timeline_built = False
        self._response_proposed = False
        return True

    def decide(self, context: ExecutionContext) -> AgentDecision:
        """
        Incident Investigation & Response Loop:
        1. Query incident metadata and current state.
        2. Compile chronological timeline from audit events.
        3. Draft response proposal requiring human approval.
        4. Finalize IncidentAgentResult.
        """
        self._process_latest_observations()

        params = self._get_initial_parameters()
        self.incident_id = params.get("incident_id", "INC-SECUROXI-001")

        # Step 1: Lookup Incident Metadata
        if not self._lookup_done:
            self._lookup_done = True
            return AgentDecision(
                decision_type=AgentActionType.USE_TOOL,
                target_tool_id="incident_lookup",
                tool_arguments={"incident_id": self.incident_id},
                reasoning_summary=f"Retrieving metadata and current state for incident '{self.incident_id}'",
            )

        # Step 2: Build Timeline
        if not self._timeline_built:
            self._timeline_built = True
            return AgentDecision(
                decision_type=AgentActionType.USE_TOOL,
                target_tool_id="incident_timeline_builder",
                tool_arguments={"incident_id": self.incident_id},
                reasoning_summary=f"Compiling chronological event timeline for incident '{self.incident_id}'",
            )

        # Step 3: Propose Response Action
        if not self._response_proposed:
            self._response_proposed = True
            proposed_action = params.get("action_type", "QUARANTINE")
            return AgentDecision(
                decision_type=AgentActionType.USE_TOOL,
                target_tool_id="incident_response_proposer",
                tool_arguments={
                    "incident_id": self.incident_id,
                    "action_type": proposed_action,
                    "target_resources": [self.affected_asset],
                    "reason": f"Incident {self.incident_id} threat containment",
                },
                reasoning_summary=f"Drafting response proposal '{proposed_action}' for incident containment",
            )

        # Step 4: Finalize Incident Report
        return AgentDecision(
            decision_type=AgentActionType.FINISH,
            reasoning_summary=f"Incident investigation complete for '{self.incident_id}'. Assembled {len(self.timeline)} timeline events.",
            confidence=0.95,
        )

    def finalize(self, context: ExecutionContext) -> AgentOutput:
        """Constructs the strongly typed AgentOutput with IncidentAgentResult."""
        summary = f"Incident '{self.incident_id}' triaged as {self.severity}. Affected asset: {self.affected_asset}."

        inc_result = IncidentAgentResult(
            incident_id=self.incident_id,
            lifecycle_state=self.lifecycle_state,
            severity=self.severity,
            timeline=self.timeline,
            correlations=self.correlations,
            proposals=self.proposals,
            summary=summary,
        )

        self.state = AgentLifecycleState.COMPLETED
        return AgentOutput(
            agent_id=self.agent_id,
            version=self.version,
            status=self.state,
            result_data=inc_result.to_dict(),
            evidence_references=[p.proposal_id for p in self.proposals],
            provenance=[f"Tenant:{context.tenant_id}", f"Agent:{self.agent_id}", f"Incident:{self.incident_id}"],
            recommended_next_steps=["REVIEW_APPROVAL_PROPOSAL", "EXECUTE_AUTHORIZED_ACTION"],
            warnings=[f"Response proposal requires human approval"] if self.proposals else [],
            confidence=0.95,
        )

    def _process_latest_observations(self):
        """Processes tool output observations."""
        for obs in self._observations:
            if obs.source == "TOOL_RESULT" and isinstance(obs.payload, dict):
                # 1. Incident Lookup
                if "affected_asset" in obs.payload:
                    self.affected_asset = obs.payload.get("affected_asset", "UNKNOWN")
                    self.severity = obs.payload.get("severity", "HIGH")
                    self.lifecycle_state = obs.payload.get("state", "TRIAGED")
                    self.correlations.append(
                        IncidentCorrelationItem(
                            entity_id=self.affected_asset,
                            entity_type="DOCUMENT",
                            relationship="AFFECTED_ASSET",
                        )
                    )

                # 2. Timeline Events
                if "events" in obs.payload and not self.timeline:
                    for ev in obs.payload.get("events", []):
                        self.timeline.append(
                            IncidentTimelineEvent(
                                timestamp=float(ev.get("timestamp", 0.0)),
                                event_name=ev.get("event_name", "EVENT"),
                                source=ev.get("source", "SYSTEM"),
                                details=ev.get("details", ""),
                            )
                        )

                # 3. Response Proposal
                if "proposal_created" in obs.payload.get("status", "").lower() or "requires_human_approval" in obs.payload:
                    self.proposals.append(
                        IncidentProposal(
                            action_type=obs.payload.get("action_type", "QUARANTINE"),
                            target_resources=obs.payload.get("target_resources", [self.affected_asset]),
                            reason=obs.payload.get("reason", "Threat containment"),
                            requires_human_approval=obs.payload.get("requires_human_approval", True),
                        )
                    )

    def _get_initial_parameters(self) -> Dict[str, Any]:
        """Extracts input parameters from initial observation."""
        for obs in self._observations:
            if obs.source == "AGENT_INPUT" and isinstance(obs.payload, dict):
                return obs.payload
        return {}
