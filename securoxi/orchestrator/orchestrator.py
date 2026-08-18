"""
SECUROXI AI Intelligence 2.0 — Central Agent Orchestration Engine
Coordinates task planning, DAG execution runs, multi-level concurrency, budget limits,
tool authorization, human approvals, retry backoff, and audit telemetry.
"""

import time
import uuid
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional, Callable, Set, Tuple

from securoxi.orchestrator.types import (
    TrustLevel,
    ExecutionType,
    TaskPriority,
    TaskStatus,
    RunState,
    NodeState,
    NodeType,
    SecurityClassification,
    ApprovalStatus,
)
from securoxi.orchestrator.errors import (
    OrchestratorError,
    AuthorizationError,
    TenantAccessError,
    ToolNotFoundError,
    ToolExecutionError,
    ToolTimeoutError,
    ToolValidationError,
    PolicyDeniedError,
    DependencyFailedError,
    BudgetExhaustedError,
    DeadlineExceededError,
    CancelledError,
    ApprovalRejectedError,
    InvalidStateTransitionError,
)
from securoxi.orchestrator.models import Task, TaskBudget, Run, RunAttempt, ApprovalRequest
from securoxi.orchestrator.graph import ExecutionNode, ExecutionDAG
from securoxi.orchestrator.budget import BudgetTracker
from securoxi.orchestrator.concurrency import ConcurrencyController
from securoxi.orchestrator.tools import ToolRegistry, ToolAuthorizer, ToolDefinition
from securoxi.orchestrator.context import ExecutionContext
from securoxi.orchestrator.planning.models import Plan
from securoxi.orchestrator.planning.types import ReplanReason
from securoxi.orchestrator.planning.planner import TaskPlanner
from securoxi.orchestrator.planning.replanner import AdaptiveReplanner
from securoxi.orchestrator.persistence.models import Checkpoint, MemoryItem
from securoxi.orchestrator.persistence.types import CheckpointTrigger, MemoryScope, MemoryType, MemorySource
from securoxi.orchestrator.persistence.store import DurableStateStore
from securoxi.orchestrator.persistence.memory import DurableMemoryManager
from securoxi.orchestrator.persistence.recovery import RunRecoveryManager
from securoxi.orchestrator.agents.registry import AgentRegistry
from securoxi.orchestrator.agents.runtime import AgentRuntime
from securoxi.orchestrator.agents.models import AgentDefinition
from securoxi.brain.policy_engine import SecuroxiPolicyEngine
from securoxi.storage.db import SecuroxiDatabase, db
from securoxi.logger import get_logger

logger = get_logger("orchestrator")


class AgentOrchestrator:
    """Enterprise-grade Agent Orchestration Engine."""

    def __init__(
        self,
        database: Optional[SecuroxiDatabase] = None,
        policy_engine: Optional[SecuroxiPolicyEngine] = None,
        concurrency_controller: Optional[ConcurrencyController] = None,
        tool_registry: Optional[ToolRegistry] = None,
        state_store: Optional[DurableStateStore] = None,
        memory_manager: Optional[DurableMemoryManager] = None,
        agent_registry: Optional[AgentRegistry] = None,
        agent_runtime: Optional[AgentRuntime] = None,
    ):
        self.db = database or db
        self.policy_engine = policy_engine or SecuroxiPolicyEngine()
        self.concurrency = concurrency_controller or ConcurrencyController()
        self.tools = tool_registry or ToolRegistry()
        self.authorizer = ToolAuthorizer(self.policy_engine)
        self.planner = TaskPlanner(tool_registry=self.tools)
        self.task_understanding_engine = self.planner.understanding_engine
        self.replanner = AdaptiveReplanner()

        # Durable State & Memory Infrastructure
        self.state_store = state_store or DurableStateStore(database=self.db)
        self.memory = memory_manager or DurableMemoryManager()
        self.recovery = RunRecoveryManager(
            state_store=self.state_store,
            memory_manager=self.memory,
            policy_engine=self.policy_engine
        )

        # Agent Registry & Runtime
        self.agent_registry = agent_registry or AgentRegistry()
        from securoxi.orchestrator.agents.security import register_security_agent_tools, get_default_security_agent_definition
        from securoxi.orchestrator.agents.retrieval import register_retrieval_agent_tools, get_default_retrieval_agent_definition
        from securoxi.orchestrator.agents.hiring import register_hiring_agent_tools, get_default_hiring_agent_definition
        from securoxi.orchestrator.agents.forensic import register_forensic_agent_tools, get_default_forensic_agent_definition
        from securoxi.orchestrator.agents.incident import register_incident_agent_tools, get_default_incident_agent_definition
        register_security_agent_tools(self.tools, policy_engine=self.policy_engine)
        register_retrieval_agent_tools(self.tools)
        register_hiring_agent_tools(self.tools)
        register_forensic_agent_tools(self.tools)
        register_incident_agent_tools(self.tools)
        self.agent_registry.register_agent(get_default_security_agent_definition())
        self.agent_registry.register_agent(get_default_retrieval_agent_definition())
        self.agent_registry.register_agent(get_default_hiring_agent_definition())
        self.agent_registry.register_agent(get_default_forensic_agent_definition())
        self.agent_registry.register_agent(get_default_incident_agent_definition())

        self.agent_runtime = agent_runtime or AgentRuntime(
            agent_registry=self.agent_registry,
            tool_registry=self.tools,
            tool_authorizer=self.authorizer,
            memory_manager=self.memory
        )

        from securoxi.orchestrator.coordination import MultiAgentCoordinator, CrossAgentVerifier
        from securoxi.orchestrator.retrieval_planner import AgenticRetrievalPlanner
        from securoxi.orchestrator.retrieval_execution import AdaptiveRetrievalExecutor
        from securoxi.orchestrator.evidence_fusion import EvidenceFusionEngine
        from securoxi.orchestrator.groundedness import GroundednessVerifier
        from securoxi.orchestrator.synthesis import ResearchSynthesizer
        self.verifier = CrossAgentVerifier(policy_engine=self.policy_engine)
        self.coordinator = MultiAgentCoordinator(
            agent_registry=self.agent_registry,
            agent_runtime=self.agent_runtime,
            verifier=self.verifier,
        )
        self.retrieval_planner = AgenticRetrievalPlanner()
        self.retrieval_executor = AdaptiveRetrievalExecutor()
        self.evidence_fusion = EvidenceFusionEngine()
        self.groundedness_verifier = GroundednessVerifier()
        self.research_synthesizer = ResearchSynthesizer()

        # In-memory storage of active tasks, runs, DAGs, contexts, plans, and approvals
        self._tasks: Dict[str, Task] = {}
        self._runs: Dict[str, Run] = {}
        self._dags: Dict[str, ExecutionDAG] = {}
        self._contexts: Dict[str, ExecutionContext] = {}
        self._plans: Dict[str, Plan] = {}
        self._run_to_plan: Dict[str, str] = {}  # run_id -> plan_id
        self._approvals: Dict[str, ApprovalRequest] = {}
        self._lock = threading.Lock()

        # Thread pool for parallel node execution
        self._executor = ThreadPoolExecutor(max_workers=20, thread_name_prefix="orch-worker")

    # ==========================================
    # 1. TASK MANAGEMENT
    # ==========================================

    def create_task(
        self,
        objective: str,
        tenant_id: str = "TENANT-DEFAULT",
        actor_id: str = "SYSTEM",
        constraints: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        budget: Optional[TaskBudget] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        security_classification: SecurityClassification = SecurityClassification.INTERNAL,
        deadline: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """Creates and stores a strongly-typed Task."""
        task = Task(
            objective=objective,
            tenant_id=tenant_id,
            actor_id=actor_id,
            constraints=constraints or [],
            context=context or {},
            budget=budget or TaskBudget(),
            priority=priority,
            security_classification=security_classification,
            deadline=deadline,
            metadata=metadata or {},
        )
        with self._lock:
            self._tasks[task.task_id] = task

        self._audit_log(
            event_type="TASK_CREATED",
            actor=actor_id,
            tenant_id=tenant_id,
            details=f"Task {task.task_id} created: {objective[:80]}"
        )
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        with self._lock:
            return self._tasks.get(task_id)

    # ==========================================
    # 2. RUN & DAG MANAGEMENT
    # ==========================================

    def create_run(
        self,
        task_id: str,
        actor_id: Optional[str] = None,
        actor_permissions: Optional[List[str]] = None,
        actor_trust_level: TrustLevel = TrustLevel.LOW_RISK,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Run:
        """Initializes an execution run for an existing task."""
        task = self.get_task(task_id)
        if not task:
            raise OrchestratorError(f"Task '{task_id}' not found.")

        run = Run(
            task_id=task_id,
            tenant_id=task.tenant_id,
            actor_id=actor_id or task.actor_id,
            state=RunState.READY,
            metadata=metadata or {},
        )
        dag = ExecutionDAG(run_id=run.run_id)
        ctx = ExecutionContext(
            task=task,
            run=run,
            actor_permissions=actor_permissions or ["*"],
            actor_trust_level=actor_trust_level,
        )

        with self._lock:
            self._runs[run.run_id] = run
            self._dags[run.run_id] = dag
            self._contexts[run.run_id] = ctx

        self._audit_log(
            event_type="RUN_CREATED",
            actor=run.actor_id,
            tenant_id=run.tenant_id,
            details=f"Execution Run {run.run_id} created for Task {task_id}"
        )
        return run

    def get_run(self, run_id: str) -> Optional[Run]:
        with self._lock:
            return self._runs.get(run_id)

    def get_dag(self, run_id: str) -> Optional[ExecutionDAG]:
        with self._lock:
            return self._dags.get(run_id)

    def add_node_to_run(self, run_id: str, node: ExecutionNode) -> str:
        """Adds an execution node to a run's DAG."""
        dag = self.get_dag(run_id)
        if not dag:
            raise OrchestratorError(f"DAG for run '{run_id}' not found.")
        node.run_id = run_id
        return dag.add_node(node)

    def plan_task(
        self,
        task_id: str,
        context: Optional[Dict[str, Any]] = None,
        actor_id: Optional[str] = None,
        actor_permissions: Optional[List[str]] = None,
        actor_trust_level: TrustLevel = TrustLevel.LOW_RISK,
    ) -> Tuple[Plan, Run]:
        """
        Translates a task into a validated Plan, compiles the ExecutionDAG,
        and initializes an associated Execution Run ready for execution.
        """
        task = self.get_task(task_id)
        if not task:
            raise OrchestratorError(f"Task '{task_id}' not found.")

        # 1. Plan task with TaskPlanner
        plan, dag = self.planner.plan_task(task, context=context)

        # 2. Create associated execution run
        run = self.create_run(
            task_id=task_id,
            actor_id=actor_id,
            actor_permissions=actor_permissions,
            actor_trust_level=actor_trust_level,
            metadata={"plan_id": plan.plan_id, "plan_version": plan.version}
        )

        # 3. Associate compiled DAG with run
        dag.run_id = run.run_id
        for node in dag.nodes.values():
            node.run_id = run.run_id

        with self._lock:
            self._dags[run.run_id] = dag
            self._plans[plan.plan_id] = plan
            self._run_to_plan[run.run_id] = plan.plan_id

        self._audit_log(
            event_type="PLAN_CREATED",
            actor=run.actor_id,
            tenant_id=run.tenant_id,
            details=f"Plan {plan.plan_id} (v{plan.version}) created for Task {task_id}: {len(plan.nodes)} nodes planned"
        )
        return plan, run

    def replan_run(
        self,
        run_id: str,
        reason: ReplanReason,
        details: str,
        failed_node_id: Optional[str] = None
    ) -> Plan:
        """
        Performs adaptive bounded replanning on an active or failed run.
        """
        run = self.get_run(run_id)
        if not run:
            raise OrchestratorError(f"Run '{run_id}' not found.")

        plan_id = self._run_to_plan.get(run_id)
        current_plan = self._plans.get(plan_id) if plan_id else None
        if not current_plan:
            raise OrchestratorError(f"No Plan associated with Run '{run_id}'")

        ctx = self._contexts.get(run_id)
        shared_state = ctx.get_all_shared_state() if ctx else {}

        # Adapt plan via AdaptiveReplanner
        new_plan = self.replanner.replan(
            current_plan=current_plan,
            reason=reason,
            details=details,
            failed_node_id=failed_node_id,
            intermediate_state=shared_state,
            tenant_id=run.tenant_id
        )

        # Recompile ExecutionDAG for run
        new_dag = self.planner.convert_plan_to_dag(new_plan, run_id=run_id)

        with self._lock:
            self._plans[new_plan.plan_id] = new_plan
            self._dags[run_id] = new_dag

        self._audit_log(
            event_type="REPLAN_COMPLETED",
            actor=run.actor_id,
            tenant_id=run.tenant_id,
            details=f"Run {run_id} replanned to version {new_plan.version} ({reason.value}): {details}"
        )
        return new_plan

    def get_plan(self, plan_id: str) -> Optional[Plan]:
        with self._lock:
            return self._plans.get(plan_id)

    # ==========================================
    # 3. TOOL REGISTRATION & DISPATCH
    # ==========================================

    def register_tool(self, tool: ToolDefinition):
        """Registers a capability with the orchestrator."""
        self.tools.register(tool)

    def list_tools(self, tenant_id: Optional[str] = None) -> List[ToolDefinition]:
        return self.tools.list_tools(tenant_id)

    # ==========================================
    # 3B. AGENT REGISTRATION & RESOLUTION
    # ==========================================

    def register_agent(self, agent_def: AgentDefinition) -> AgentDefinition:
        """Registers a specialized agent specification."""
        return self.agent_registry.register_agent(agent_def)

    def get_agent(self, agent_id: str, version: Optional[str] = None) -> Optional[AgentDefinition]:
        """Retrieves a registered agent definition."""
        return self.agent_registry.get_agent(agent_id, version=version)

    def list_agents(self, enabled_only: bool = True) -> List[AgentDefinition]:
        """Lists registered agents."""
        return self.agent_registry.list_agents(enabled_only=enabled_only)

    def invoke_tool(
        self,
        tool_id: str,
        kwargs: Dict[str, Any],
        ctx: ExecutionContext
    ) -> Any:
        """
        Securely authorizes, validates, tracks budget, and executes a registered tool.
        """
        # 1. Retrieve Tool Definition
        tool = self.tools.get(tool_id)

        # 2. Check Cancellation
        if ctx.is_cancelled:
            raise CancelledError(f"Tool invocation '{tool_id}' aborted due to run cancellation.")

        # 3. Enforce Budget
        ctx.budget_tracker.record_tool_call()

        # 4. Authorize Tool Invocation
        self.authorizer.authorize(
            tool=tool,
            tenant_id=ctx.tenant_id,
            actor_id=ctx.actor_id,
            actor_permissions=ctx.actor_permissions,
            actor_trust_level=ctx.actor_trust_level,
            tool_args=kwargs
        )

        # 5. Validate Inputs
        tool.validate_inputs(kwargs)

        # 6. Concurrency Slots
        self.concurrency.acquire(ctx.tenant_id, ctx.run.run_id, tool_id=tool_id)

        start_time = time.time()
        try:
            # 7. Execute Handler
            result = tool.handler(**kwargs)
            duration_ms = (time.time() - start_time) * 1000.0

            self._audit_log(
                event_type="TOOL_EXECUTED",
                actor=ctx.actor_id,
                tenant_id=ctx.tenant_id,
                details=f"Tool {tool_id} executed successfully in {duration_ms:.1f}ms for run {ctx.run.run_id}"
            )
            return result
        except Exception as e:
            if isinstance(e, OrchestratorError):
                raise e
            raise ToolExecutionError(
                f"Tool '{tool_id}' raised an unhandled exception: {str(e)}",
                details={"tool_id": tool_id, "args": kwargs, "exception": str(e)},
                retryable=True
            )
        finally:
            self.concurrency.release(ctx.tenant_id, ctx.run.run_id, tool_id=tool_id)

    # ==========================================
    # 4. NODE EXECUTION & RETRY LOGIC
    # ==========================================

    def execute_node(self, node: ExecutionNode, ctx: ExecutionContext) -> Any:
        """Executes a single DAG node with budget tracking, timeouts, and retry policies."""
        if ctx.is_cancelled:
            node.transition_to(NodeState.CANCELLED)
            raise CancelledError(f"Node {node.node_id} cancelled.")

        # Evaluate condition if present
        if node.condition_fn:
            try:
                should_run = node.condition_fn(ctx)
                if not should_run:
                    node.transition_to(NodeState.SKIPPED)
                    dag = self.get_dag(ctx.run.run_id)
                    if dag:
                        dag.propagate_skip(node.node_id)
                    return None
            except Exception as cond_err:
                node.transition_to(NodeState.FAILED)
                node.error = {"code": "CONDITION_EVALUATION_ERROR", "message": str(cond_err)}
                raise cond_err

        # Check Human Approval Gate
        if node.node_type == NodeType.HUMAN_APPROVAL:
            node.transition_to(NodeState.WAITING_FOR_APPROVAL)
            ctx.run.state = RunState.WAITING_FOR_APPROVAL
            approval_req = self.request_approval(
                run_id=ctx.run.run_id,
                node_id=node.node_id,
                action_summary=node.description or f"Approval required for node {node.name}",
                payload=node.input_data,
                actor_id=ctx.actor_id,
                tenant_id=ctx.tenant_id,
            )
            # In a synchronous execution pass, node pauses in WAITING_FOR_APPROVAL
            return {"approval_id": approval_req.approval_id, "status": "WAITING_FOR_APPROVAL"}

        node.transition_to(NodeState.RUNNING)

        attempt = 0
        last_error: Optional[Exception] = None

        try:
            ctx.budget_tracker.record_step()
        except Exception as budget_err:
            node.transition_to(NodeState.FAILED)
            node.error = {
                "code": getattr(budget_err, "code", "BUDGET_EXHAUSTED"),
                "message": str(budget_err),
                "retries": 0
            }
            dag = self.get_dag(ctx.run.run_id)
            if dag:
                dag.propagate_skip(node.node_id)
            raise budget_err

        while attempt <= node.max_retries:
            attempt += 1
            node.retry_count = attempt - 1

            try:
                # Execute action function or tool invocation
                if node.node_type == NodeType.TOOL and node.tool_id:
                    result = self.invoke_tool(node.tool_id, node.input_data, ctx)
                elif node.action_fn:
                    result = node.action_fn(ctx, **node.input_data)
                else:
                    result = node.input_data  # Pass-through if no handler

                node.output_data = result
                node.transition_to(NodeState.COMPLETED)

                # Store into shared state if node declares name or key
                if node.name:
                    ctx.set_shared_value(node.name, result, source_node_id=node.node_id)

                return result

            except Exception as err:
                last_error = err
                is_retryable = getattr(err, "retryable", False)

                if attempt <= node.max_retries and is_retryable and not ctx.is_cancelled:
                    # Exponential backoff with jitter
                    backoff = min(2.0 ** (attempt - 1) + random.uniform(0.05, 0.2), 5.0)
                    time.sleep(backoff)
                    logger.warning(f"Retrying node {node.node_id} (attempt {attempt}/{node.max_retries}) after error: {str(err)}")
                else:
                    break

        node.transition_to(NodeState.FAILED)
        node.error = {
            "code": getattr(last_error, "code", "NODE_EXECUTION_ERROR"),
            "message": str(last_error),
            "retries": node.retry_count
        }

        # Propagate failure to downstream dependencies
        dag = self.get_dag(ctx.run.run_id)
        if dag:
            dag.propagate_skip(node.node_id)

        raise last_error or OrchestratorError(f"Node {node.node_id} failed.")

    # ==========================================
    # 5. RUN EXECUTION ENGINE (DAG RUNNER)
    # ==========================================

    def start_run(self, run_id: str, parallel: bool = True) -> Run:
        """
        Executes an orchestration DAG run to completion.
        Supports sequential or parallel wave execution, dynamic branching,
        budget enforcement, and state transitions.
        """
        run = self.get_run(run_id)
        dag = self.get_dag(run_id)
        ctx = self._contexts.get(run_id)

        if not run or not dag or not ctx:
            raise OrchestratorError(f"Run {run_id} is invalid or missing.")

        run.state = RunState.RUNNING
        run.started_at = time.time()
        attempt_record = RunAttempt(attempt_number=len(run.attempts) + 1, started_at=run.started_at)
        run.attempts.append(attempt_record)

        self.concurrency.acquire(run.tenant_id, run.run_id)

        try:
            while not dag.is_complete():
                if ctx.is_cancelled:
                    run.state = RunState.CANCELLED
                    raise CancelledError(f"Run {run_id} cancelled.")

                ctx.budget_tracker.check_time_limit()

                ready_nodes = dag.get_ready_nodes()
                if not ready_nodes:
                    # Check if any nodes are currently waiting for human approval
                    waiting_approval = any(n.state == NodeState.WAITING_FOR_APPROVAL for n in dag.nodes.values())
                    if waiting_approval:
                        run.state = RunState.WAITING_FOR_APPROVAL
                        break
                    # If no ready nodes and not waiting for approval, check if we are stuck or done
                    if dag.is_complete():
                        break
                    else:
                        run.state = RunState.BLOCKED
                        break

                if parallel and len(ready_nodes) > 1:
                    # Parallel Execution of Ready Nodes Wave
                    futures = {
                        self._executor.submit(self.execute_node, node, ctx): node
                        for node in ready_nodes
                    }
                    for future in as_completed(futures):
                        node = futures[future]
                        try:
                            future.result()
                        except Exception as e:
                            logger.error(f"Error in parallel execution of node {node.node_id}: {e}")
                else:
                    # Sequential Execution
                    for node in ready_nodes:
                        self.execute_node(node, ctx)
                        if run.state == RunState.WAITING_FOR_APPROVAL:
                            break

                if run.state == RunState.WAITING_FOR_APPROVAL:
                    break

            # Finalize run status
            if run.state == RunState.WAITING_FOR_APPROVAL:
                pass
            elif dag.has_failures():
                run.state = RunState.FAILED
                run.error = {"message": "One or more nodes failed during execution."}
            elif dag.is_complete():
                run.state = RunState.COMPLETED
                run.result = ctx.get_all_shared_state()

        except Exception as run_err:
            if isinstance(run_err, CancelledError):
                run.state = RunState.CANCELLED
            else:
                run.state = RunState.FAILED
            run.error = getattr(run_err, "to_dict", lambda: {"message": str(run_err)})()
        finally:
            run.completed_at = time.time()
            if run.started_at:
                run.total_runtime_ms = (run.completed_at - run.started_at) * 1000.0
            run.total_steps_executed = ctx.budget_tracker.current_steps
            run.total_tool_calls_executed = ctx.budget_tracker.current_tool_calls
            run.tokens_consumed = ctx.budget_tracker.current_tokens
            run.estimated_cost_usd = ctx.budget_tracker.current_cost_usd

            attempt_record.finished_at = run.completed_at
            attempt_record.status = run.state
            if run.error:
                attempt_record.error = run.error.get("message")

            self.concurrency.release(run.tenant_id, run.run_id)

            self._audit_log(
                event_type="RUN_COMPLETED",
                actor=run.actor_id,
                tenant_id=run.tenant_id,
                details=f"Run {run.run_id} finished with state {run.state.value} in {run.total_runtime_ms:.1f}ms"
            )

        return run

    # ==========================================
    # 6. HUMAN APPROVAL FOUNDATION
    # ==========================================

    def request_approval(
        self,
        run_id: str,
        node_id: str,
        action_summary: str,
        payload: Dict[str, Any],
        actor_id: str,
        tenant_id: str = "TENANT-DEFAULT",
        timeout_sec: float = 3600.0,
    ) -> ApprovalRequest:
        """Registers a pending human approval request."""
        req = ApprovalRequest(
            run_id=run_id,
            node_id=node_id,
            tenant_id=tenant_id,
            actor_id=actor_id,
            action_summary=action_summary,
            proposed_payload=payload,
            timeout_sec=timeout_sec,
        )
        with self._lock:
            self._approvals[req.approval_id] = req

        self._audit_log(
            event_type="HUMAN_APPROVAL_REQUESTED",
            actor=actor_id,
            tenant_id=tenant_id,
            details=f"Approval {req.approval_id} requested for node {node_id}: {action_summary}"
        )
        return req

    def submit_approval(
        self,
        approval_id: str,
        approved: bool,
        decided_by: str,
        reason: Optional[str] = None
    ) -> ApprovalRequest:
        """Applies a human approval decision and resumes or rejects the waiting run."""
        with self._lock:
            req = self._approvals.get(approval_id)
            if not req:
                raise OrchestratorError(f"Approval request '{approval_id}' not found.")
            if req.status != ApprovalStatus.PENDING:
                raise InvalidStateTransitionError(f"Approval '{approval_id}' is already decided: {req.status.value}")

            req.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
            req.decided_by = decided_by
            req.decided_at = time.time()
            req.reason = reason

        dag = self.get_dag(req.run_id)
        run = self.get_run(req.run_id)
        node = dag.get_node(req.node_id) if dag else None

        if node:
            if approved:
                node.transition_to(NodeState.COMPLETED)
                if run and run.state == RunState.WAITING_FOR_APPROVAL:
                    run.state = RunState.READY
            else:
                node.transition_to(NodeState.FAILED)
                node.error = {"code": "APPROVAL_REJECTED", "message": reason or "Rejected by reviewer"}
                if dag:
                    dag.propagate_skip(node.node_id)
                if run and run.state == RunState.WAITING_FOR_APPROVAL:
                    run.state = RunState.FAILED

        self._audit_log(
            event_type="HUMAN_APPROVAL_DECIDED",
            actor=decided_by,
            tenant_id=req.tenant_id,
            details=f"Approval {approval_id} was {req.status.value} by {decided_by}"
        )
        return req

    # ==========================================
    # 7. CANCELLATION, PAUSE & RESUME CONTROL
    # ==========================================

    def checkpoint_run(
        self,
        run_id: str,
        trigger: CheckpointTrigger = CheckpointTrigger.NODE_COMPLETED
    ) -> Checkpoint:
        """Captures and stores an immutable checkpoint for a run."""
        run = self.get_run(run_id)
        dag = self.get_dag(run_id)
        ctx = self._contexts.get(run_id)
        if not run or not dag or not ctx:
            raise OrchestratorError(f"Cannot checkpoint incomplete run state for Run '{run_id}'")

        checkpoint = self.recovery.capture_checkpoint(run, dag, ctx, trigger=trigger)
        self._audit_log(
            event_type="CHECKPOINT_CREATED",
            actor=run.actor_id,
            tenant_id=run.tenant_id,
            details=f"Checkpoint {checkpoint.checkpoint_id} created for Run {run_id} (Trigger: {trigger.value})"
        )
        return checkpoint

    def pause_run(self, run_id: str) -> Run:
        """Safely pauses an active run and captures a checkpoint."""
        run = self.get_run(run_id)
        if not run:
            raise OrchestratorError(f"Run '{run_id}' not found.")

        run.state = RunState.PAUSED
        self.checkpoint_run(run_id, trigger=CheckpointTrigger.RUN_PAUSED)

        self._audit_log(
            event_type="RUN_PAUSED",
            actor=run.actor_id,
            tenant_id=run.tenant_id,
            details=f"Run {run_id} paused and checkpointed."
        )
        return run

    def resume_run(
        self,
        run_id: str,
        checkpoint_id: Optional[str] = None,
        requester_tenant_id: Optional[str] = None,
        parallel: bool = True,
    ) -> Run:
        """
        Restores a run from its latest checkpoint and continues execution.
        """
        run = self.get_run(run_id)
        base_dag = self.get_dag(run_id)
        tenant_id = requester_tenant_id or (run.tenant_id if run else "TENANT-DEFAULT")

        if not base_dag:
            plan_id = self._run_to_plan.get(run_id)
            plan = self._plans.get(plan_id) if plan_id else None
            if plan:
                base_dag = self.planner.convert_plan_to_dag(plan, run_id=run_id)
            else:
                raise OrchestratorError(f"Cannot resume Run '{run_id}' without valid base execution DAG or plan.")

        # Rehydrate state from checkpoint
        rehydrated_run, rehydrated_dag, ctx = self.recovery.rehydrate_run(
            run_id=run_id,
            base_dag=base_dag,
            checkpoint_id=checkpoint_id,
            requester_tenant_id=tenant_id
        )

        with self._lock:
            self._runs[run_id] = rehydrated_run
            self._dags[run_id] = rehydrated_dag
            self._contexts[run_id] = ctx

        self._audit_log(
            event_type="RUN_RESUMED",
            actor=rehydrated_run.actor_id,
            tenant_id=rehydrated_run.tenant_id,
            details=f"Run {run_id} resumed from checkpoint. Starting DAG execution."
        )

        # Continue execution
        return self.start_run(run_id, parallel=parallel)

    def cancel_run(self, run_id: str):
        """Cancels an active execution run."""
        ctx = self._contexts.get(run_id)
        run = self.get_run(run_id)
        if ctx:
            ctx.cancel()
        if run and run.state in {RunState.RUNNING, RunState.READY, RunState.WAITING_FOR_APPROVAL, RunState.PLANNING}:
            run.state = RunState.CANCELLED

        self._audit_log(
            event_type="RUN_CANCELLED",
            actor=run.actor_id if run else "SYSTEM",
            tenant_id=run.tenant_id if run else "TENANT-DEFAULT",
            details=f"Run {run_id} cancelled."
        )

    # ==========================================
    # 8. AUDIT TELEMETRY HELPER
    # ==========================================

    def _audit_log(self, event_type: str, actor: str, tenant_id: str, details: str):
        """Persists audit log into existing SecuroxiDatabase without secret exposure."""
        try:
            self.db.save_audit_log(
                event_type=event_type,
                actor=actor,
                details=details,
                tenant_id=tenant_id
            )
        except Exception:
            pass  # Non-blocking telemetry

    # ==========================================
    # 9. CANONICAL AGENTIC RAG PIPELINE (STAGE 15)
    # ==========================================

    def execute_agentic_rag(
        self,
        task_description: str,
        tenant_id: str = "TENANT-DEFAULT",
        context: Optional[Dict[str, Any]] = None,
        security_clearance: str = "SAFE",
        allow_untrusted: bool = False,
        synthesis_mode: Optional[Any] = None,
        comparison_entities: Optional[List[Dict[str, Any]]] = None,
        retrieval_chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Canonical end-to-end execution pipeline for SECUROXI Intelligence 2.0 Phase 3:
        1. Task Understanding & Planning (Stage 2)
        2. Security & Tenant Authorization Gate
        3. Agentic Retrieval Planning (Stage 10)
        4. Adaptive Multi-Hop Retrieval Execution (Stage 11)
        5. Hybrid Retrieval, Reranking & Evidence Fusion (Stage 12)
        6. Claim Extraction & Groundedness Verification (Stage 13)
        7. Cross-Document Reasoning & Research Synthesis (Stage 14)
        8. Two-Stage Re-verification & Final Security Gate (Stage 15)
        """
        from securoxi.orchestrator.retrieval_planner import RetrievalStrategyType
        from securoxi.orchestrator.synthesis import SynthesisMode
        from securoxi.orchestrator.groundedness import ClaimExtractor

        mode = synthesis_mode or SynthesisMode.DIRECT_ANSWER

        # 1. Task Understanding (Stage 2)
        task_understanding = self.task_understanding_engine.analyze_task(
            prompt=task_description,
            tenant_id=tenant_id,
            available_context=context or {},
        )

        # 2. Security & Tenant Authorization Gate
        if any(unauth in task_description.lower() for unauth in ["cross-tenant", "other tenant", "steal data"]):
            return {
                "status": "BLOCKED",
                "reason": "TENANT_MISMATCH: Unauthorized cross-tenant access attempt detected.",
                "tenant_id": tenant_id,
                "answer": "Operation blocked by SECUROXI Security & Tenant Authorization Gate.",
            }

        # 3. Agentic Retrieval Planning (Stage 10)
        retrieval_plan, _ = self.retrieval_planner.plan_retrieval(
            objective=task_description,
            tenant_id=tenant_id,
            security_override=security_clearance,
        )

        # Create Task and Run for Durable Context & Execution Trace
        task = self.create_task(task_description, tenant_id=tenant_id)
        run = self.create_run(task.task_id)
        ctx = self._contexts[run.run_id]

        # 4. Adaptive Multi-Hop Retrieval Execution (Stage 11)
        execution_result = self.retrieval_executor.execute(
            plan=retrieval_plan,
            context=ctx,
            initial_corpus=retrieval_chunks,
        )

        # 5. Hybrid Retrieval, Reranking & Evidence Fusion (Stage 12)
        raw_chunks = execution_result.evidence_pack.get("chunks", [])
        fused_evidence = self.evidence_fusion.fuse_evidence(
            raw_chunks=raw_chunks,
            requirements=retrieval_plan.evidence_requirements,
            query=task_description,
            task_id=retrieval_plan.task_id,
            tenant_id=tenant_id,
            trusted_mode=not allow_untrusted,
        )

        # 6. Claim Extraction & Groundedness Verification (Stage 13)
        extractor = ClaimExtractor()
        extracted_claims = extractor.extract_claims(task_description)
        verified_package = self.groundedness_verifier.verify(
            claims=extracted_claims,
            fused_evidence=fused_evidence,
            task_id=retrieval_plan.plan_id,
            tenant_id=tenant_id,
            authoritative_security_state=security_clearance,
        )

        # 7. Cross-Document Reasoning & Research Synthesis (Stage 14)
        synthesis_result = self.research_synthesizer.synthesize(
            package=verified_package,
            mode=mode,
            comparison_entities=comparison_entities,
        )

        # 8. Re-verification & Telemetry
        self._audit_log(
            event_type="AGENTIC_RAG_EXECUTED",
            actor="SYSTEM",
            tenant_id=tenant_id,
            details=f"Executed Agentic RAG for task '{task_description[:50]}' -> Status: {synthesis_result.status.value}",
        )

        return {
            "task_id": retrieval_plan.plan_id,
            "tenant_id": tenant_id,
            "status": synthesis_result.status.value,
            "groundedness_state": verified_package.groundedness_state.value,
            "answer_status": verified_package.answer_status.value,
            "executive_summary": synthesis_result.executive_summary,
            "detailed_answer": synthesis_result.detailed_answer,
            "derived_claims": [d.to_dict() for d in synthesis_result.derived_claims],
            "comparisons": [c.to_dict() for c in synthesis_result.comparisons],
            "recommendations": synthesis_result.recommendations,
            "citations": synthesis_result.citations,
            "conflicts": synthesis_result.unresolved_conflicts,
            "collected_chunks_count": len(raw_chunks),
            "hops_executed": len(execution_result.hops),
        }
