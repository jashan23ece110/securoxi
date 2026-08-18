"""
SECUROXI AI Intelligence 2.0 — Pluggable Agent Abstraction Interface
Defines the future agent contract (initialize, decide, execute, validate, finalize)
enabling safe, bounded agent plugins without hardcoding specialized agents into the orchestrator.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from securoxi.orchestrator.types import TrustLevel
from securoxi.orchestrator.context import ExecutionContext


class BaseAgent(ABC):
    """Abstract base class for all SECUROXI intelligent agents."""

    def __init__(
        self,
        agent_id: str,
        role: str,
        description: str,
        allowed_tools: List[str],
        trust_level: TrustLevel = TrustLevel.CONTROLLED,
        version: str = "1.0.0",
    ):
        self.agent_id = agent_id
        self.role = role
        self.description = description
        self.allowed_tools = allowed_tools
        self.trust_level = trust_level
        self.version = version

    @abstractmethod
    def initialize(self, ctx: ExecutionContext, config: Optional[Dict[str, Any]] = None):
        """Prepares the agent for execution in a specific run context."""
        pass

    @abstractmethod
    def decide(self, ctx: ExecutionContext, observation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates current observations and decides the next step or tool invocation.
        Must return a structured decision payload.
        """
        pass

    @abstractmethod
    def execute(self, ctx: ExecutionContext, step_input: Dict[str, Any]) -> Any:
        """Executes the chosen step within budget and tenant constraints."""
        pass

    @abstractmethod
    def validate(self, ctx: ExecutionContext, result: Any) -> bool:
        """Validates agent output against safety and schema standards."""
        pass

    @abstractmethod
    def finalize(self, ctx: ExecutionContext) -> Dict[str, Any]:
        """Synthesizes final agent results for downstream consumption."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "description": self.description,
            "allowed_tools": self.allowed_tools,
            "trust_level": self.trust_level.value,
            "version": self.version,
        }
