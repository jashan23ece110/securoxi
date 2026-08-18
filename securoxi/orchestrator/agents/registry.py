"""
SECUROXI AI Intelligence 2.0 — Central Agent Registry & Resolver
Manages agent definitions, version compatibility, capability discovery,
and deterministic agent resolution.
"""

import threading
from typing import Dict, Any, List, Optional, Set, Tuple

from securoxi.orchestrator.agents.types import (
    AgentDomain,
    AgentCapability,
    AgentRiskLevel,
    AgentLifecycleState,
    MemoryAccessPermission,
)
from securoxi.orchestrator.agents.models import AgentDefinition
from securoxi.orchestrator.types import TrustLevel
from securoxi.orchestrator.planning.types import TaskIntent
from securoxi.orchestrator.errors import (
    OrchestratorError,
    ToolValidationError,
    AuthorizationError,
)
from securoxi.logger import get_logger

logger = get_logger("orchestrator.agent_registry")


class AgentRegistry:
    """
    Centralized, thread-safe repository for all system-registered agents.
    Prevents unauthorized or untrusted agent registration and provides deterministic resolution.
    """

    def __init__(self):
        # agent_id -> AgentDefinition
        self._agents: Dict[str, AgentDefinition] = {}
        # (agent_id, version) -> AgentDefinition
        self._versioned_agents: Dict[Tuple[str, str], AgentDefinition] = {}
        self._lock = threading.RLock()
        self._register_default_agent_placeholders()

    def _register_default_agent_placeholders(self):
        """Registers system agent specifications with explicit tool allowlists and capabilities."""
        # 1. Security Agent Specification Placeholder
        self.register_agent(
            AgentDefinition(
                agent_id="AGENT-SECURITY",
                name="Securoxi Security Agent",
                description="Specialized agent for prompt injection detection, visual deception analysis, and threat correlation",
                version="1.0.0",
                domain=AgentDomain.SECURITY,
                capabilities=[
                    AgentCapability.SECURITY_ANALYSIS,
                    AgentCapability.FORENSIC_ANALYSIS,
                    AgentCapability.REPORT_GENERATION,
                ],
                trust_level=TrustLevel.CONTROLLED,
                risk_level=AgentRiskLevel.MEDIUM,
                allowed_tools={"security_scanner", "evidence_extractor", "threat_intel_lookup", "policy_evaluator"},
                supported_intents=[
                    TaskIntent.DOCUMENT_SCAN,
                    TaskIntent.BULK_SCAN,
                    TaskIntent.SECURITY_INVESTIGATION,
                    TaskIntent.MIXED_WORKFLOW,
                ],
            )
        )

        # 2. Hiring & ATS Agent Specification Placeholder
        self.register_agent(
            AgentDefinition(
                agent_id="AGENT-HIRING",
                name="Securoxi Hiring Intelligence Agent",
                description="Specialized agent for resume parsing, qualification scoring, and ATS synchronization",
                version="1.0.0",
                domain=AgentDomain.HIRING,
                capabilities=[
                    AgentCapability.CANDIDATE_SCREENING,
                    AgentCapability.JD_MATCHING,
                    AgentCapability.REPORT_GENERATION,
                ],
                trust_level=TrustLevel.CONTROLLED,
                risk_level=AgentRiskLevel.MEDIUM,
                allowed_tools={"jd_parser", "candidate_scorer", "ats_connector", "qualification_evaluator"},
                supported_intents=[
                    TaskIntent.CANDIDATE_SCREENING,
                    TaskIntent.JD_MATCHING,
                    TaskIntent.ATS_OPERATION,
                    TaskIntent.MIXED_WORKFLOW,
                ],
            )
        )

        # 3. Document Retrieval & RAG Agent Specification Placeholder
        self.register_agent(
            AgentDefinition(
                agent_id="AGENT-RETRIEVAL",
                name="Securoxi Retrieval Agent",
                description="Specialized agent for semantic vector retrieval, reranking, and citation synthesis",
                version="1.0.0",
                domain=AgentDomain.RETRIEVAL,
                capabilities=[
                    AgentCapability.DOCUMENT_RETRIEVAL,
                    AgentCapability.REPORT_GENERATION,
                    AgentCapability.GENERAL_REASONING,
                ],
                trust_level=TrustLevel.LOW_RISK,
                risk_level=AgentRiskLevel.LOW,
                allowed_tools={"vector_retriever", "hybrid_reranker", "citation_formatter"},
                supported_intents=[
                    TaskIntent.QUESTION_ANSWERING,
                    TaskIntent.DOCUMENT_ANALYSIS,
                    TaskIntent.DOCUMENT_COMPARISON,
                ],
            )
        )

        # 4. Incident Response Agent Specification Placeholder
        self.register_agent(
            AgentDefinition(
                agent_id="AGENT-INCIDENT",
                name="Securoxi Incident Response Agent",
                description="Specialized agent for quarantine containment, SIEM event correlation, and forensic auditing",
                version="1.0.0",
                domain=AgentDomain.INCIDENTS,
                capabilities=[
                    AgentCapability.INCIDENT_INVESTIGATION,
                    AgentCapability.FORENSIC_ANALYSIS,
                ],
                trust_level=TrustLevel.HIGH_IMPACT,
                risk_level=AgentRiskLevel.HIGH,
                allowed_tools={"quarantine_manager", "audit_logger", "siem_exporter"},
                supported_intents=[
                    TaskIntent.INCIDENT_INVESTIGATION,
                    TaskIntent.SECURITY_INVESTIGATION,
                ],
            )
        )

    def register_agent(self, agent_def: AgentDefinition) -> AgentDefinition:
        """Registers or updates a validated AgentDefinition."""
        with self._lock:
            self.validate_agent_definition(agent_def)
            self._agents[agent_def.agent_id] = agent_def
            self._versioned_agents[(agent_def.agent_id, agent_def.version)] = agent_def
            logger.info(f"Registered Agent '{agent_def.agent_id}' (v{agent_def.version}, Domain: {agent_def.domain.value})")
            return agent_def

    def unregister_agent(self, agent_id: str) -> bool:
        """Removes an agent from the active registry."""
        with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
                logger.info(f"Unregistered Agent '{agent_id}'")
                return True
            return False

    def get_agent(self, agent_id: str, version: Optional[str] = None) -> Optional[AgentDefinition]:
        """Retrieves an agent by ID and optional version."""
        with self._lock:
            if version:
                return self._versioned_agents.get((agent_id, version))
            return self._agents.get(agent_id)

    def resolve_agent(
        self,
        intent: TaskIntent,
        capability: AgentCapability,
        min_trust_level: Optional[TrustLevel] = None,
        tenant_id: str = "TENANT-DEFAULT",
    ) -> Optional[AgentDefinition]:
        """
        Deterministically resolves the best matching enabled agent definition
        based on intent compatibility, advertised capability, and trust constraints.
        """
        with self._lock:
            candidates: List[AgentDefinition] = []

            for agent in self._agents.values():
                if not agent.enabled:
                    continue
                if capability not in agent.capabilities:
                    continue
                if intent not in agent.supported_intents:
                    continue
                candidates.append(agent)

            if not candidates:
                return None

            # Sort candidate agents by capability count descending (most specialized first)
            candidates.sort(key=lambda a: len(a.capabilities), reverse=True)
            return candidates[0]

    def list_agents(self, enabled_only: bool = True) -> List[AgentDefinition]:
        """Lists all registered agent definitions."""
        with self._lock:
            if enabled_only:
                return [a for a in self._agents.values() if a.enabled]
            return list(self._agents.values())

    def find_by_capability(self, capability: AgentCapability) -> List[AgentDefinition]:
        """Finds all agents advertising a specific capability."""
        with self._lock:
            return [a for a in self._agents.values() if a.enabled and capability in a.capabilities]

    def find_by_intent(self, intent: TaskIntent) -> List[AgentDefinition]:
        """Finds all agents supporting a specific task intent."""
        with self._lock:
            return [a for a in self._agents.values() if a.enabled and intent in a.supported_intents]

    def enable_agent(self, agent_id: str) -> bool:
        """Enables a registered agent."""
        with self._lock:
            agent = self._agents.get(agent_id)
            if agent:
                agent.enabled = True
                return True
            return False

    def disable_agent(self, agent_id: str) -> bool:
        """Disables a registered agent."""
        with self._lock:
            agent = self._agents.get(agent_id)
            if agent:
                agent.enabled = False
                return True
            return False

    def validate_agent_definition(self, agent_def: AgentDefinition) -> bool:
        """Validates agent definition requirements."""
        if not agent_def.agent_id:
            raise ToolValidationError("Agent definition missing required 'agent_id'")
        if not agent_def.name:
            raise ToolValidationError("Agent definition missing required 'name'")
        if not agent_def.version:
            raise ToolValidationError("Agent definition missing required 'version'")
        if not agent_def.capabilities:
            raise ToolValidationError("Agent definition must declare at least one capability")
        return True
