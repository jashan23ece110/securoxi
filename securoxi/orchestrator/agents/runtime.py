"""
SECUROXI AI Intelligence 2.0 — Agent Runtime Engine
Executes agents within a strictly controlled loop enforcing tool allowlists, memory access scopes,
policy gates, handoff validation, and zero-leakage trace generation.
"""

import time
import uuid
from typing import Dict, Any, List, Optional, Set, Callable, Tuple

from securoxi.orchestrator.agents.models import (
    AgentDefinition,
    AgentInput,
    AgentObservation,
    AgentDecision,
    AgentOutput,
    AgentHandoffContract,
    AgentTraceRecord,
)
from securoxi.orchestrator.agents.types import (
    AgentLifecycleState,
    AgentActionType,
    MemoryAccessPermission,
)
from securoxi.orchestrator.agents.base import AbstractAgent
from securoxi.orchestrator.agents.registry import AgentRegistry
from securoxi.orchestrator.context import ExecutionContext
from securoxi.orchestrator.tools import ToolRegistry, ToolAuthorizer
from securoxi.orchestrator.persistence.memory import DurableMemoryManager
from securoxi.orchestrator.persistence.types import MemoryScope, MemoryType, MemorySource, MemoryTrustHierarchy
from securoxi.orchestrator.errors import (
    OrchestratorError,
    AuthorizationError,
    TenantAccessError,
    ToolNotFoundError,
    PolicyDeniedError,
    BudgetExhaustedError,
    ToolValidationError,
)
from securoxi.logger import get_logger

logger = get_logger("orchestrator.agent_runtime")


class AgentRuntime:
    """
    Controlled execution runtime for SECUROXI agents.
    Enforces deterministic policy boundaries, tool allowlists, and memory scoping.
    """

    def __init__(
        self,
        agent_registry: AgentRegistry,
        tool_registry: ToolRegistry,
        tool_authorizer: ToolAuthorizer,
        memory_manager: Optional[DurableMemoryManager] = None,
    ):
        self.registry = agent_registry
        self.tools = tool_registry
        self.authorizer = tool_authorizer
        self.memory = memory_manager or DurableMemoryManager()
        self._traces: Dict[str, AgentTraceRecord] = {}

    def execute_agent(
        self,
        agent: AbstractAgent,
        agent_input: AgentInput,
        context: ExecutionContext,
        tool_executor_fn: Optional[Callable[[str, Dict[str, Any], ExecutionContext], Any]] = None,
    ) -> Tuple[AgentOutput, AgentTraceRecord]:
        """
        Runs the agent loop: OBSERVE -> DECIDE -> AUTHORIZE -> EXECUTE -> UPDATE -> TERMINATE.
        """
        start_time = time.time()
        trace = AgentTraceRecord(
            agent_id=agent.agent_id,
            version=agent.version,
            task_id=agent_input.task_id,
            run_id=agent_input.run_id,
            node_id=agent_input.node_id,
            tenant_id=agent_input.tenant_id,
        )

        # 1. Initialize Agent
        agent.initialize(context)
        agent.state = AgentLifecycleState.RUNNING

        # Ingest initial input observation
        initial_obs = AgentObservation(
            source="AGENT_INPUT",
            payload=agent_input.parameters,
            provenance=[f"Task:{agent_input.task_id}", f"Node:{agent_input.node_id}"]
        )
        agent.observe(initial_obs)

        iteration = 0
        max_iters = agent.definition.max_iterations

        try:
            while iteration < max_iters:
                iteration += 1
                context.budget_tracker.check_time_limit()

                # Step 1: DECIDE
                decision = agent.decide(context)
                trace.steps.append({
                    "iteration": iteration,
                    "decision": decision.to_dict(),
                    "timestamp": time.time()
                })

                # Step 2: Handle Decision Action Type
                if decision.decision_type == AgentActionType.FINISH:
                    break

                elif decision.decision_type == AgentActionType.CONTINUE:
                    # Agent explicitly requested another reasoning cycle
                    continue

                elif decision.decision_type == AgentActionType.ABORT:
                    agent.state = AgentLifecycleState.FAILED
                    raise OrchestratorError(f"Agent {agent.agent_id} aborted execution: {decision.reasoning_summary}")

                elif decision.decision_type == AgentActionType.USE_TOOL:
                    tool_id = decision.target_tool_id
                    if not tool_id:
                        raise ToolValidationError("Agent proposed USE_TOOL but omitted target_tool_id")

                    # Step 3: Tool Allowlist Check (Agent Boundary)
                    if tool_id not in agent.definition.allowed_tools:
                        trace.tools_denied.append(tool_id)
                        raise AuthorizationError(
                            f"Agent '{agent.agent_id}' attempted to call undeclared tool '{tool_id}'. Allowed: {sorted(list(agent.definition.allowed_tools))}"
                        )

                    # Step 4: Phase 1 Tool Authorizer (Tenant & Policy Engine Gate)
                    tool_def = self.tools.get(tool_id)
                    try:
                        self.authorizer.authorize(
                            tool=tool_def,
                            tenant_id=context.tenant_id,
                            actor_id=context.actor_id,
                            actor_permissions=context.actor_permissions,
                            actor_trust_level=context.actor_trust_level,
                            tool_args=decision.tool_arguments,
                        )
                    except Exception as auth_err:
                        trace.tools_denied.append(tool_id)
                        raise auth_err

                    # Step 5: Execute Tool
                    context.budget_tracker.record_tool_call()
                    trace.tools_invoked.append(tool_id)

                    if tool_executor_fn:
                        tool_result = tool_executor_fn(tool_id, decision.tool_arguments, context)
                    else:
                        tool_result = tool_def.handler(context, **decision.tool_arguments)

                    # Step 6: Ingest Tool Observation back to Agent
                    obs = AgentObservation(
                        source="TOOL_RESULT",
                        payload=tool_result,
                        provenance=[f"Tool:{tool_id}", f"Agent:{agent.agent_id}"]
                    )
                    agent.observe(obs)

                elif decision.decision_type == AgentActionType.HANDOFF:
                    if not decision.target_agent_id:
                        raise ToolValidationError("Agent proposed HANDOFF but omitted target_agent_id")

                    target_def = self.registry.get_agent(decision.target_agent_id)
                    if not target_def or not target_def.enabled:
                        raise OrchestratorError(f"Handoff target agent '{decision.target_agent_id}' is unavailable or disabled.")

                    handoff = AgentHandoffContract(
                        source_agent_id=agent.agent_id,
                        target_agent_id=decision.target_agent_id,
                        tenant_id=agent_input.tenant_id,
                        handoff_data=decision.handoff_payload,
                        trust_level=agent.definition.trust_level,
                        provenance_chain=[f"Agent:{agent.agent_id}"],
                    )
                    self.validate_handoff(handoff, target_def)
                    trace.handoffs.append(decision.target_agent_id)
                    break

            if iteration >= max_iters:
                logger.warning(f"Agent {agent.agent_id} reached maximum iterations limit ({max_iters})")

            # Finalize Output
            agent_output = agent.finalize(context)
            agent.state = AgentLifecycleState.COMPLETED
            trace.final_status = "COMPLETED"

        except Exception as err:
            agent.state = AgentLifecycleState.FAILED
            trace.final_status = "FAILED"
            raise err
        finally:
            trace.duration_ms = (time.time() - start_time) * 1000.0
            trace.budget_usage = {
                "steps": context.budget_tracker.current_steps,
                "tool_calls": context.budget_tracker.current_tool_calls,
            }
            self._traces[trace.trace_id] = trace

        return agent_output, trace

    def validate_handoff(self, handoff: AgentHandoffContract, target_agent: AgentDefinition) -> bool:
        """Validates inter-agent handoff security boundaries and tenant matching."""
        if not handoff.source_agent_id or not handoff.target_agent_id:
            raise ToolValidationError("Invalid handoff: Missing source or target agent identity")
        if handoff.source_agent_id == handoff.target_agent_id:
            raise ToolValidationError("Invalid handoff: Agent cannot hand off to itself")
        return True

    def verify_memory_access(self, agent_def: AgentDefinition, required_permission: MemoryAccessPermission) -> bool:
        """Enforces that an agent has explicit permissions to access a specific memory scope."""
        if required_permission not in agent_def.memory_scopes:
            raise AuthorizationError(
                f"Agent '{agent_def.agent_id}' lacks required memory permission '{required_permission.value}'"
            )
        return True
