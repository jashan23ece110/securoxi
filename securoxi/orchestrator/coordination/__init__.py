"""
SECUROXI AI Intelligence 2.0 — Multi-Agent Coordination Package
Exports MultiAgentCoordinator, CrossAgentVerifier, models, and types.
"""

from securoxi.orchestrator.coordination.types import (
    AuthorityLevel,
    HandoffStatus,
    VerificationState,
    ConflictType,
    CoordinationCompletionStatus,
)
from securoxi.orchestrator.coordination.models import (
    AgentHandoff,
    AgentResultEnvelope,
    CoordinationConflict,
    CoordinationStep,
    CoordinationPlan,
    VerificationResult,
    ConsensusResult,
    CoordinationResult,
)
from securoxi.orchestrator.coordination.verifier import CrossAgentVerifier
from securoxi.orchestrator.coordination.coordinator import MultiAgentCoordinator

__all__ = [
    "AuthorityLevel",
    "HandoffStatus",
    "VerificationState",
    "ConflictType",
    "CoordinationCompletionStatus",
    "AgentHandoff",
    "AgentResultEnvelope",
    "CoordinationConflict",
    "CoordinationStep",
    "CoordinationPlan",
    "VerificationResult",
    "ConsensusResult",
    "CoordinationResult",
    "CrossAgentVerifier",
    "MultiAgentCoordinator",
]
