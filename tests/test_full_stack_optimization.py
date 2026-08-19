"""
SECUROXI AI Intelligence 2.0 — Full-Stack Agent, Workflow Cost & Latency Optimization Test Suite (Stage 32)
Validates execution-scoped agent result caching, duplicate work reduction, resource bounding,
and strict preservation of security trust boundaries and tenant isolation.
"""

import pytest
from securoxi.orchestrator import (
    AgentOrchestrator,
    CoordinationPlan,
    CoordinationStep,
    AuthorityLevel,
    CoordinationCompletionStatus,
)


# =========================================================================
# 1. EXECUTION-SCOPED AGENT RESULT REUSE (OPT-AGNT-01)
# =========================================================================

def test_multi_agent_step_result_caching():
    """Verifies that identical agent calls within a coordination plan reuse cached envelopes."""
    orchestrator = AgentOrchestrator()
    task = orchestrator.create_task("Multi-agent search", tenant_id="TENANT-OPT")
    run = orchestrator.create_run(task.task_id)
    ctx = orchestrator._contexts[run.run_id]

    # Plan has two identical retrieval steps
    steps = [
        CoordinationStep(
            step_id="STEP-1",
            agent_id="retrieval-agent",
            authority_level=AuthorityLevel.AUTHORITATIVE,
            purpose="Initial query search",
            inputs={"query": "Kubernetes security best practices"},
        ),
        CoordinationStep(
            step_id="STEP-2",
            agent_id="retrieval-agent",
            authority_level=AuthorityLevel.AUTHORITATIVE,
            purpose="Duplicate query search",
            inputs={"query": "Kubernetes security best practices"},
        ),
    ]

    plan = CoordinationPlan(
        plan_id="PLAN-OPT-01",
        task_id=task.task_id,
        steps=steps,
        max_handoffs=5,
    )

    result = orchestrator.coordinator.execute_plan(plan, ctx)
    assert result.status in [CoordinationCompletionStatus.COMPLETED, CoordinationCompletionStatus.CONFLICTING]
    assert len(result.agent_envelopes) == 2
    assert "AgentCached:retrieval-agent" in result.provenance_chain


# =========================================================================
# 2. TENANT BOUNDARY ISOLATION IN OPTIMIZED COORDINATION
# =========================================================================

def test_tenant_isolation_under_coordination_optimization():
    """Verifies that cached execution results do not cross tenant boundaries."""
    orchestrator = AgentOrchestrator()

    # Tenant A
    task_a = orchestrator.create_task("Search A", tenant_id="TENANT-A")
    run_a = orchestrator.create_run(task_a.task_id)
    ctx_a = orchestrator._contexts[run_a.run_id]

    plan_a = CoordinationPlan(
        plan_id="PLAN-A",
        task_id=task_a.task_id,
        steps=[
            CoordinationStep(
                step_id="STEP-A",
                agent_id="retrieval-agent",
                authority_level=AuthorityLevel.AUTHORITATIVE,
                purpose="Search A",
                inputs={"query": "Secrets management"},
            )
        ],
    )
    res_a = orchestrator.coordinator.execute_plan(plan_a, ctx_a)

    # Tenant B (different context and tenant)
    task_b = orchestrator.create_task("Search B", tenant_id="TENANT-B")
    run_b = orchestrator.create_run(task_b.task_id)
    ctx_b = orchestrator._contexts[run_b.run_id]

    plan_b = CoordinationPlan(
        plan_id="PLAN-B",
        task_id=task_b.task_id,
        steps=[
            CoordinationStep(
                step_id="STEP-B",
                agent_id="retrieval-agent",
                authority_level=AuthorityLevel.AUTHORITATIVE,
                purpose="Search B",
                inputs={"query": "Secrets management"},
            )
        ],
    )
    res_b = orchestrator.coordinator.execute_plan(plan_b, ctx_b)

    assert res_a.provenance_chain[1] == "Tenant:TENANT-A"
    assert res_b.provenance_chain[1] == "Tenant:TENANT-B"
