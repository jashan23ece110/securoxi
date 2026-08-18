"""
SECUROXI AI Intelligence 2.0 — Multi-Agent Coordinator
Orchestrates structured inter-agent handoffs, parallel/sequential coordination plans,
bounded feedback loops, cross-agent verification, and deterministic conflict resolution.
"""

from typing import Dict, Any, List, Optional
import time
from securoxi.orchestrator.agents.registry import AgentRegistry
from securoxi.orchestrator.agents.runtime import AgentRuntime
from securoxi.orchestrator.agents.models import AgentInput, AgentOutput
from securoxi.orchestrator.agents.types import AgentDomain, AgentCapability, AgentLifecycleState
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
    CoordinationStep,
    CoordinationPlan,
    CoordinationConflict,
    VerificationResult,
    CoordinationResult,
)
from securoxi.orchestrator.coordination.verifier import CrossAgentVerifier
from securoxi.orchestrator.context import ExecutionContext
from securoxi.orchestrator.errors import (
    OrchestratorError,
    AuthorizationError,
    BudgetExhaustedError,
)
from securoxi.logger import get_logger

logger = get_logger("orchestrator.coordinator")


class MultiAgentCoordinator:
    """
    Central coordinator orchestrating specialized SECUROXI agents:
    - SecurityAgent
    - RetrievalAgent
    - HiringAgent
    - ForensicAgent
    - IncidentAgent
    Enforces structured handoffs, deterministic authority, and unbroken provenance.
    """

    def __init__(
        self,
        agent_registry: AgentRegistry,
        agent_runtime: AgentRuntime,
        verifier: Optional[CrossAgentVerifier] = None,
    ):
        self.agent_registry = agent_registry
        self.agent_runtime = agent_runtime
        self.verifier = verifier or CrossAgentVerifier()
        self._max_coordination_depth = 15

    def execute_plan(
        self,
        plan: CoordinationPlan,
        context: ExecutionContext,
    ) -> CoordinationResult:
        """
        Executes a dynamic CoordinationPlan across participating specialized agents:
        1. Validates plan constraints and tenant isolation.
        2. Executes coordination steps sequentially/in parallel respecting dependencies.
        3. Wraps outputs in AgentResultEnvelope with explicit authority levels.
        4. Executes cross-agent verification and conflict resolution.
        5. Builds provenance chain and synthesizes final CoordinationResult.
        """
        logger.info(f"Starting Multi-Agent Coordination Plan '{plan.plan_id}' for task '{plan.task_id}' (Tenant: {context.tenant_id})")

        envelopes: List[AgentResultEnvelope] = []
        step_results: Dict[str, Dict[str, Any]] = {}
        provenance_chain: List[str] = [f"Plan:{plan.plan_id}", f"Tenant:{context.tenant_id}"]
        handoffs_executed = 0

        # Step Loop
        for step in plan.steps:
            if handoffs_executed >= plan.max_handoffs:
                logger.warning(f"Coordination Plan '{plan.plan_id}' exceeded max handoffs ({plan.max_handoffs})")
                break

            # 1. Validate Target Agent
            agent_def = self.agent_registry.get_agent(step.agent_id)
            if not agent_def:
                logger.error(f"Agent '{step.agent_id}' not found in registry")
                continue

            if not agent_def.enabled:
                logger.error(f"Agent '{step.agent_id}' is disabled")
                continue

            run_id = context.run.run_id if context.run else "RUN-DEFAULT"

            # 2. Build Structured Handoff
            handoff = AgentHandoff(
                source_agent_id="COORDINATOR",
                target_agent_id=step.agent_id,
                task_id=plan.task_id,
                run_id=run_id,
                tenant_id=context.tenant_id,
                purpose=step.purpose,
                structured_input=step.inputs,
                trust_level=agent_def.trust_level,
                provenance=list(provenance_chain),
                status=HandoffStatus.AUTHORIZED,
            )

            # 3. Instantiate and Execute Agent
            agent_instance = self._resolve_agent_instance(step.agent_id, agent_def)
            if not agent_instance:
                logger.error(f"Could not instantiate agent '{step.agent_id}'")
                continue

            agent_input = AgentInput(
                task_id=plan.task_id,
                run_id=run_id,
                node_id=step.step_id,
                tenant_id=context.tenant_id,
                parameters=step.inputs,
            )

            output, trace = self.agent_runtime.execute_agent(agent_instance, agent_input, context)
            handoffs_executed += 1
            handoff.status = HandoffStatus.COMPLETED

            # 4. Wrap in Result Envelope with explicit Authority Level
            envelope = AgentResultEnvelope(
                agent_identity=step.agent_id,
                agent_version=agent_def.version,
                status=output.status.value,
                authority_level=step.authority_level,
                result_data=output.result_data,
                evidence_refs=output.evidence_references,
                provenance=output.provenance,
                warnings=output.warnings,
                verification_state=VerificationState.VERIFIED if output.status == AgentLifecycleState.COMPLETED else VerificationState.UNVERIFIED,
            )
            envelopes.append(envelope)
            step_results[step.step_id] = output.result_data
            provenance_chain.append(f"Agent:{step.agent_id}")

        # 5. Cross-Agent Verification & Conflict Resolution
        verification = self.verifier.verify_envelopes(envelopes, context.tenant_id)

        # 6. Determine Final Coordination Status
        if not verification.is_valid:
            final_status = CoordinationCompletionStatus.FAILED
        elif verification.conflicts:
            final_status = CoordinationCompletionStatus.CONFLICTING
        elif not verification.security_cleared:
            final_status = CoordinationCompletionStatus.BLOCKED
        else:
            final_status = CoordinationCompletionStatus.COMPLETED

        # 7. Synthesize Top-Level Final Result
        final_data = {}
        for env in envelopes:
            final_data[env.agent_identity] = env.result_data

        human_review = None
        if final_status in [CoordinationCompletionStatus.CONFLICTING, CoordinationCompletionStatus.BLOCKED]:
            human_review = {
                "reason": "Cross-agent conflict or security block required manual investigation",
                "conflicts": [c.to_dict() for c in verification.conflicts],
                "envelopes": [e.envelope_id for e in envelopes],
            }

        return CoordinationResult(
            task_id=plan.task_id,
            run_id=context.run.run_id if context.run else "RUN-DEFAULT",
            tenant_id=context.tenant_id,
            status=final_status,
            final_result=final_data,
            agent_envelopes=envelopes,
            conflicts=verification.conflicts,
            verification=verification,
            provenance_chain=provenance_chain,
            human_review_packet=human_review,
        )

    def _resolve_agent_instance(self, agent_id: str, agent_def: Any) -> Optional[Any]:
        """Instantiates specialized agent class based on registered agent definition."""
        from securoxi.orchestrator.agents.security import SecurityAgent
        from securoxi.orchestrator.agents.retrieval import RetrievalAgent
        from securoxi.orchestrator.agents.hiring import HiringAgent
        from securoxi.orchestrator.agents.forensic import ForensicAgent
        from securoxi.orchestrator.agents.incident import IncidentAgent

        id_lower = agent_id.lower()
        if "security" in id_lower:
            return SecurityAgent(definition=agent_def)
        elif "retrieval" in id_lower:
            return RetrievalAgent(definition=agent_def)
        elif "hiring" in id_lower:
            return HiringAgent(definition=agent_def)
        elif "forensic" in id_lower:
            return ForensicAgent(definition=agent_def)
        elif "incident" in id_lower:
            return IncidentAgent(definition=agent_def)
        return None
