"""
SECUROXI AI Intelligence 2.0 — Agent Orchestrator Core Test Suite
Validates Task/Run models, DAG execution, sequential/parallel/conditional workflows,
budget enforcement, timeouts, cancellation, concurrency, tool permissions, human approvals,
adversarial attacks, and performance benchmarks.
"""

import time
import pytest
from securoxi.orchestrator import (
    AgentOrchestrator,
    Task,
    TaskBudget,
    Run,
    RunState,
    NodeState,
    NodeType,
    ExecutionType,
    TrustLevel,
    TaskPriority,
    ApprovalStatus,
    ExecutionNode,
    ExecutionDAG,
    ToolDefinition,
    ToolParameter,
    OrchestratorError,
    AuthorizationError,
    TenantAccessError,
    ToolValidationError,
    PolicyDeniedError,
    BudgetExhaustedError,
    DeadlineExceededError,
    CancelledError,
    ConcurrencyLimitExceededError,
)
from securoxi.brain.policy_engine import SecuroxiPolicyEngine, PolicyRule, PolicyDecisionAction


@pytest.fixture
def orchestrator():
    """Returns a fresh AgentOrchestrator instance with policy engine."""
    engine = SecuroxiPolicyEngine()
    # Add a sample blocking rule for testing
    engine.register_rule(
        PolicyRule(
            rule_id="BLOCK_QUARANTINED_TOOLS",
            priority=100,
            name="Block Dangerous Operations",
            description="Blocks quarantined tool targets",
            action=PolicyDecisionAction.BLOCK,
            condition=lambda ctx: ctx.target == "quarantined_tool",
        )
    )
    orch = AgentOrchestrator(policy_engine=engine)
    return orch


# =========================================================================
# 1. TASK & RUN LIFECYCLE TESTS
# =========================================================================

def test_task_creation_and_run_initialization(orchestrator):
    """Verifies strong typing and isolation between Tasks and Runs."""
    budget = TaskBudget(max_steps=25, max_tool_calls=50, max_runtime_sec=120.0)
    task = orchestrator.create_task(
        objective="Scan candidate collection and score against JD",
        tenant_id="TENANT-ACME",
        actor_id="USER-ALICE",
        budget=budget,
        priority=TaskPriority.HIGH,
    )

    assert task.task_id.startswith("TASK-")
    assert task.tenant_id == "TENANT-ACME"
    assert task.budget.max_steps == 25

    # Create multiple runs for same task
    run1 = orchestrator.create_run(task.task_id, actor_id="USER-ALICE")
    run2 = orchestrator.create_run(task.task_id, actor_id="USER-ALICE")

    assert run1.run_id != run2.run_id
    assert run1.task_id == task.task_id
    assert run2.task_id == task.task_id
    assert run1.state == RunState.READY


# =========================================================================
# 2. SEQUENTIAL DAG EXECUTION TESTS
# =========================================================================

def test_sequential_dag_execution(orchestrator):
    """Tests linear sequential execution (A -> B -> C) with shared state passing."""
    task = orchestrator.create_task("Linear Workflow", tenant_id="TENANT-01")
    run = orchestrator.create_run(task.task_id)

    node_a = ExecutionNode(
        name="step_a",
        node_type=NodeType.TRANSFORM,
        action_fn=lambda ctx: {"data": "hello"}
    )
    node_b = ExecutionNode(
        name="step_b",
        node_type=NodeType.TRANSFORM,
        dependencies=[node_a.node_id],
        action_fn=lambda ctx: {"data": ctx.get_shared_value("step_a")["data"] + " world"}
    )
    node_c = ExecutionNode(
        name="step_c",
        node_type=NodeType.FINALIZE,
        dependencies=[node_b.node_id],
        action_fn=lambda ctx: ctx.get_shared_value("step_b")["data"].upper()
    )

    orchestrator.add_node_to_run(run.run_id, node_a)
    orchestrator.add_node_to_run(run.run_id, node_b)
    orchestrator.add_node_to_run(run.run_id, node_c)

    completed_run = orchestrator.start_run(run.run_id, parallel=False)

    assert completed_run.state == RunState.COMPLETED
    assert completed_run.total_steps_executed == 3
    assert completed_run.result["step_c"] == "HELLO WORLD"
    assert node_a.state == NodeState.COMPLETED
    assert node_b.state == NodeState.COMPLETED
    assert node_c.state == NodeState.COMPLETED


# =========================================================================
# 3. PARALLEL DAG EXECUTION TESTS (FAN-OUT / FAN-IN)
# =========================================================================

def test_parallel_dag_fan_out_fan_in(orchestrator):
    """Tests parallel fan-out across multiple worker nodes and fan-in aggregation."""
    task = orchestrator.create_task("Parallel Fan-Out", tenant_id="TENANT-01")
    run = orchestrator.create_run(task.task_id)

    # Initial input node
    prep_node = ExecutionNode(
        name="prep",
        node_type=NodeType.TRANSFORM,
        action_fn=lambda ctx: [10, 20, 30, 40]
    )
    orchestrator.add_node_to_run(run.run_id, prep_node)

    # 4 Parallel worker nodes
    worker_ids = []
    for i, val in enumerate([10, 20, 30, 40]):
        wnode = ExecutionNode(
            name=f"worker_{i}",
            node_type=NodeType.TRANSFORM,
            dependencies=[prep_node.node_id],
            input_data={"multiplier": 2, "value": val},
            action_fn=lambda ctx, multiplier, value: value * multiplier
        )
        orchestrator.add_node_to_run(run.run_id, wnode)
        worker_ids.append(wnode.node_id)

    # Aggregator fan-in node
    agg_node = ExecutionNode(
        name="aggregate",
        node_type=NodeType.FINALIZE,
        dependencies=worker_ids,
        action_fn=lambda ctx: sum(ctx.get_shared_value(f"worker_{i}") for i in range(4))
    )
    orchestrator.add_node_to_run(run.run_id, agg_node)

    start_t = time.time()
    completed_run = orchestrator.start_run(run.run_id, parallel=True)
    duration = time.time() - start_t

    assert completed_run.state == RunState.COMPLETED
    assert completed_run.result["aggregate"] == (10*2 + 20*2 + 30*2 + 40*2) # 200
    assert duration < 2.0  # Fast parallel execution


# =========================================================================
# 4. CONDITIONAL BRANCHING & SKIP PROPAGATION
# =========================================================================

def test_conditional_branching_and_skip(orchestrator):
    """Verifies conditional predicate execution and skip propagation on unselected paths."""
    task = orchestrator.create_task("Conditional Workflow", tenant_id="TENANT-01")
    run = orchestrator.create_run(task.task_id)

    decision_node = ExecutionNode(
        name="decision",
        node_type=NodeType.DECISION,
        action_fn=lambda ctx: {"verdict": "SAFE"}
    )

    # Branch A: Should execute because verdict == SAFE
    branch_safe = ExecutionNode(
        name="branch_safe",
        node_type=NodeType.TRANSFORM,
        dependencies=[decision_node.node_id],
        condition_fn=lambda ctx: ctx.get_shared_value("decision")["verdict"] == "SAFE",
        action_fn=lambda ctx: "Processed Safe Document"
    )

    # Branch B: Should skip because verdict != HIGH_RISK
    branch_risky = ExecutionNode(
        name="branch_risky",
        node_type=NodeType.TRANSFORM,
        dependencies=[decision_node.node_id],
        condition_fn=lambda ctx: ctx.get_shared_value("decision")["verdict"] == "HIGH_RISK",
        action_fn=lambda ctx: "Processed Risky Document"
    )

    # Downstream of Branch B: Should be skipped
    downstream_risky = ExecutionNode(
        name="downstream_risky",
        node_type=NodeType.FINALIZE,
        dependencies=[branch_risky.node_id],
        action_fn=lambda ctx: "Quarantine Log"
    )

    orchestrator.add_node_to_run(run.run_id, decision_node)
    orchestrator.add_node_to_run(run.run_id, branch_safe)
    orchestrator.add_node_to_run(run.run_id, branch_risky)
    orchestrator.add_node_to_run(run.run_id, downstream_risky)

    completed_run = orchestrator.start_run(run.run_id, parallel=False)

    assert completed_run.state == RunState.COMPLETED
    assert branch_safe.state == NodeState.COMPLETED
    assert branch_risky.state == NodeState.SKIPPED
    assert downstream_risky.state == NodeState.SKIPPED
    assert completed_run.result["branch_safe"] == "Processed Safe Document"


# =========================================================================
# 5. TOOL REGISTRATION & SCHEMA VALIDATION
# =========================================================================

def test_tool_registration_and_validation(orchestrator):
    """Validates tool registration, parameter type checking, and schema enforcement."""
    def add_numbers(x: int, y: int) -> int:
        return x + y

    tool = ToolDefinition(
        tool_id="math_add",
        name="Add Numbers",
        description="Adds two integers",
        handler=add_numbers,
        parameters=[
            ToolParameter(name="x", param_type="int", required=True),
            ToolParameter(name="y", param_type="int", required=True),
        ],
        trust_level=TrustLevel.LOW_RISK,
    )
    orchestrator.register_tool(tool)

    task = orchestrator.create_task("Tool Test", tenant_id="TENANT-01")
    run = orchestrator.create_run(task.task_id)

    node = ExecutionNode(
        name="add_step",
        node_type=NodeType.TOOL,
        tool_id="math_add",
        input_data={"x": 15, "y": 25},
    )
    orchestrator.add_node_to_run(run.run_id, node)
    completed_run = orchestrator.start_run(run.run_id)

    assert completed_run.state == RunState.COMPLETED
    assert node.output_data == 40
    assert completed_run.total_tool_calls_executed == 1


def test_tool_missing_required_parameter(orchestrator):
    """Ensures ToolValidationError is raised when required inputs are omitted."""
    tool = ToolDefinition(
        tool_id="lookup_user",
        name="Lookup User",
        description="Lookup user by ID",
        handler=lambda user_id: f"User {user_id}",
        parameters=[ToolParameter(name="user_id", required=True)],
    )
    orchestrator.register_tool(tool)

    task = orchestrator.create_task("Param Test", tenant_id="TENANT-01")
    run = orchestrator.create_run(task.task_id)

    node = ExecutionNode(
        name="lookup_step",
        node_type=NodeType.TOOL,
        tool_id="lookup_user",
        input_data={},  # Missing user_id
    )
    orchestrator.add_node_to_run(run.run_id, node)
    completed_run = orchestrator.start_run(run.run_id)

    assert completed_run.state == RunState.FAILED
    assert node.state == NodeState.FAILED


# =========================================================================
# 6. TOOL PERMISSION, TENANT & POLICY GATING
# =========================================================================

def test_tenant_boundary_isolation(orchestrator):
    """Ensures a tenant cannot invoke a tool scoped strictly to another tenant."""
    tool = ToolDefinition(
        tool_id="tenant_secret_tool",
        name="Tenant Secret Tool",
        description="Tenant specific tool",
        handler=lambda: "secret_data",
        tenant_scope="TENANT-ACME",
    )
    orchestrator.register_tool(tool)

    # Actor from TENANT-OTHER tries to invoke TENANT-ACME tool
    task = orchestrator.create_task("Cross Tenant Attempt", tenant_id="TENANT-OTHER")
    run = orchestrator.create_run(task.task_id)

    node = ExecutionNode(
        name="breach_step",
        node_type=NodeType.TOOL,
        tool_id="tenant_secret_tool",
        input_data={},
    )
    orchestrator.add_node_to_run(run.run_id, node)
    completed_run = orchestrator.start_run(run.run_id)

    assert completed_run.state == RunState.FAILED
    assert node.state == NodeState.FAILED


def test_policy_engine_rejection_for_high_impact_tool(orchestrator):
    """Ensures deterministic Policy Engine blocks high-impact tools that violate policies."""
    tool = ToolDefinition(
        tool_id="quarantined_tool",
        name="Quarantined Tool",
        description="A quarantined operation",
        handler=lambda: "done",
        trust_level=TrustLevel.HIGH_IMPACT,
    )
    orchestrator.register_tool(tool)

    task = orchestrator.create_task("Policy Gate Test", tenant_id="TENANT-01")
    run = orchestrator.create_run(task.task_id, actor_trust_level=TrustLevel.CONTROLLED)

    node = ExecutionNode(
        name="blocked_step",
        node_type=NodeType.TOOL,
        tool_id="quarantined_tool",
        input_data={},
    )
    orchestrator.add_node_to_run(run.run_id, node)
    completed_run = orchestrator.start_run(run.run_id)

    assert completed_run.state == RunState.FAILED
    assert node.state == NodeState.FAILED


# =========================================================================
# 7. BUDGET & RESOURCE LIMIT ENFORCEMENT
# =========================================================================

def test_step_budget_exhaustion(orchestrator):
    """Ensures orchestrator halts execution when step budget is exceeded."""
    budget = TaskBudget(max_steps=2)
    task = orchestrator.create_task("Budget Step Test", tenant_id="TENANT-01", budget=budget)
    run = orchestrator.create_run(task.task_id)

    n1 = ExecutionNode(name="s1", action_fn=lambda ctx: 1)
    n2 = ExecutionNode(name="s2", dependencies=[n1.node_id], action_fn=lambda ctx: 2)
    n3 = ExecutionNode(name="s3", dependencies=[n2.node_id], action_fn=lambda ctx: 3)

    orchestrator.add_node_to_run(run.run_id, n1)
    orchestrator.add_node_to_run(run.run_id, n2)
    orchestrator.add_node_to_run(run.run_id, n3)

    completed_run = orchestrator.start_run(run.run_id, parallel=False)

    assert completed_run.state == RunState.FAILED
    assert n1.state == NodeState.COMPLETED
    assert n2.state == NodeState.COMPLETED
    assert n3.state == NodeState.FAILED


def test_tool_call_budget_exhaustion(orchestrator):
    """Ensures orchestrator halts when tool invocation budget is exhausted."""
    tool = ToolDefinition(
        tool_id="repeat_tool",
        name="Repeat Tool",
        description="Dummy tool",
        handler=lambda: "ok"
    )
    orchestrator.register_tool(tool)

    budget = TaskBudget(max_tool_calls=1)
    task = orchestrator.create_task("Tool Budget Test", tenant_id="TENANT-01", budget=budget)
    run = orchestrator.create_run(task.task_id)

    n1 = ExecutionNode(name="t1", node_type=NodeType.TOOL, tool_id="repeat_tool")
    n2 = ExecutionNode(name="t2", node_type=NodeType.TOOL, tool_id="repeat_tool", dependencies=[n1.node_id])

    orchestrator.add_node_to_run(run.run_id, n1)
    orchestrator.add_node_to_run(run.run_id, n2)

    completed_run = orchestrator.start_run(run.run_id, parallel=False)

    assert completed_run.state == RunState.FAILED
    assert n1.state == NodeState.COMPLETED
    assert n2.state == NodeState.FAILED


# =========================================================================
# 8. CANCELLATION & GRACEFUL SHUTDOWN
# =========================================================================

def test_run_cancellation(orchestrator):
    """Verifies that cancelling an active run gracefully halts execution."""
    task = orchestrator.create_task("Cancel Test", tenant_id="TENANT-01")
    run = orchestrator.create_run(task.task_id)

    def slow_action(ctx):
        time.sleep(0.05)
        orchestrator.cancel_run(run.run_id)
        return "first_done"

    n1 = ExecutionNode(name="slow_step", action_fn=slow_action)
    n2 = ExecutionNode(name="blocked_step", dependencies=[n1.node_id], action_fn=lambda ctx: "never")

    orchestrator.add_node_to_run(run.run_id, n1)
    orchestrator.add_node_to_run(run.run_id, n2)

    completed_run = orchestrator.start_run(run.run_id, parallel=False)

    assert completed_run.state == RunState.CANCELLED


# =========================================================================
# 9. HUMAN APPROVAL GATE WORKFLOW
# =========================================================================

def test_human_approval_workflow(orchestrator):
    """Tests blocking on human approval node and resumption upon reviewer decision."""
    task = orchestrator.create_task("Approval Workflow", tenant_id="TENANT-01")
    run = orchestrator.create_run(task.task_id)

    step1 = ExecutionNode(
        name="initial_analysis",
        action_fn=lambda ctx: {"quarantine_candidate": "CAND-09"}
    )
    approval_node = ExecutionNode(
        name="human_review",
        node_type=NodeType.HUMAN_APPROVAL,
        description="Approve quarantine of Candidate CAND-09",
        dependencies=[step1.node_id],
        input_data={"candidate_id": "CAND-09"}
    )
    final_step = ExecutionNode(
        name="apply_action",
        dependencies=[approval_node.node_id],
        action_fn=lambda ctx: "Action Applied Successfully"
    )

    orchestrator.add_node_to_run(run.run_id, step1)
    orchestrator.add_node_to_run(run.run_id, approval_node)
    orchestrator.add_node_to_run(run.run_id, final_step)

    # First pass: runs up to human approval and pauses
    run_paused = orchestrator.start_run(run.run_id, parallel=False)

    assert run_paused.state == RunState.WAITING_FOR_APPROVAL
    assert step1.state == NodeState.COMPLETED
    assert approval_node.state == NodeState.WAITING_FOR_APPROVAL
    assert final_step.state == NodeState.PENDING

    # Find the approval request ID
    approval_id = list(orchestrator._approvals.keys())[0]

    # Human reviewer submits approval
    orchestrator.submit_approval(
        approval_id=approval_id,
        approved=True,
        decided_by="SECURITY_ADMIN_BOB",
        reason="Verified prompt injection in candidate resume."
    )

    # Resume run to completion
    run_resumed = orchestrator.start_run(run.run_id, parallel=False)

    assert run_resumed.state == RunState.COMPLETED
    assert approval_node.state == NodeState.COMPLETED
    assert final_step.state == NodeState.COMPLETED
    assert run_resumed.result["apply_action"] == "Action Applied Successfully"


# =========================================================================
# 10. ADVERSARIAL & PERFORMANCE BENCHMARK
# =========================================================================

def test_adversarial_untrusted_actor_elevation(orchestrator):
    """Ensures UNTRUSTED actors cannot execute HIGH_IMPACT actions."""
    high_impact_tool = ToolDefinition(
        tool_id="purge_database",
        name="Purge Database",
        description="Deletes all tenant data",
        handler=lambda: "purged",
        trust_level=TrustLevel.HIGH_IMPACT,
    )
    orchestrator.register_tool(high_impact_tool)

    task = orchestrator.create_task("Attack Test", tenant_id="TENANT-01")
    run = orchestrator.create_run(task.task_id, actor_trust_level=TrustLevel.UNTRUSTED)

    node = ExecutionNode(
        name="malicious_step",
        node_type=NodeType.TOOL,
        tool_id="purge_database",
    )
    orchestrator.add_node_to_run(run.run_id, node)
    completed_run = orchestrator.start_run(run.run_id)

    assert completed_run.state == RunState.FAILED


def test_orchestrator_dispatch_performance_benchmark(orchestrator):
    """Benchmarks node scheduling and dispatch latency (< 5ms per node overhead)."""
    task = orchestrator.create_task("Benchmark", tenant_id="TENANT-01")
    run = orchestrator.create_run(task.task_id)

    prev_id = None
    for i in range(20):
        node = ExecutionNode(
            name=f"bench_{i}",
            dependencies=[prev_id] if prev_id else [],
            action_fn=lambda ctx: i
        )
        orchestrator.add_node_to_run(run.run_id, node)
        prev_id = node.node_id

    start_time = time.time()
    completed_run = orchestrator.start_run(run.run_id, parallel=False)
    total_time = time.time() - start_time

    assert completed_run.state == RunState.COMPLETED
    avg_node_time = total_time / 20.0
    # Average dispatch latency should be well under 10ms per node
    assert avg_node_time < 0.010, f"Average dispatch time {avg_node_time*1000:.2f}ms exceeded 10ms"
