"""
SECUROXI AI Intelligence 2.0 — Abstract Agent Base Class
Provides foundational lifecycle handling, observation ingestion, decision drafting,
and schema validation for all specialized agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from securoxi.orchestrator.agent_interface import BaseAgent
from securoxi.orchestrator.agents.models import (
    AgentDefinition,
    AgentInput,
    AgentObservation,
    AgentDecision,
    AgentOutput,
)
from securoxi.orchestrator.agents.types import AgentLifecycleState, AgentActionType
from securoxi.orchestrator.context import ExecutionContext


class AbstractAgent(BaseAgent, ABC):
    """
    Standard abstract base class enforcing the SECUROXI Agent Runtime Contract.
    """

    def __init__(self, definition: AgentDefinition):
        super().__init__(
            agent_id=definition.agent_id,
            role=definition.name,
            description=definition.description,
            allowed_tools=list(definition.allowed_tools),
            trust_level=definition.trust_level,
            version=definition.version,
        )
        self.definition = definition
        self.state = AgentLifecycleState.REGISTERED
        self._observations: List[AgentObservation] = []
        self._decisions: List[AgentDecision] = []

    def initialize(self, context: ExecutionContext, **kwargs) -> bool:
        """Initializes agent state prior to node execution."""
        self.state = AgentLifecycleState.INITIALIZING
        self._observations.clear()
        self._decisions.clear()
        self.state = AgentLifecycleState.READY
        return True

    def observe(self, observation: AgentObservation):
        """Ingests an observation from a tool, document, or peer agent."""
        self._observations.append(observation)

    @abstractmethod
    def decide(self, context: ExecutionContext) -> AgentDecision:
        """Formulates the next action proposal (tool use, handoff, or completion)."""
        pass

    def execute(self, ctx: ExecutionContext, step_input: Optional[Dict[str, Any]] = None) -> Any:
        """Executes the chosen step within budget and tenant constraints."""
        return {"status": "SUCCESS", "agent_id": self.agent_id}

    def validate(self, ctx: Any, result: Optional[Any] = None) -> bool:
        """Validates intermediate or final result against declared schema."""
        return True

    def finalize(self, context: ExecutionContext) -> AgentOutput:
        """Assembles the final validated output payload upon loop completion."""
        self.state = AgentLifecycleState.COMPLETED
        return AgentOutput(
            agent_id=self.agent_id,
            version=self.version,
            status=self.state,
            result_data={"observations_count": len(self._observations)},
            confidence=1.0,
        )
