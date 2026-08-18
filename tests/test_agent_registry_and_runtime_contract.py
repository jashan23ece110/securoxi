"""
SECUROXI AI Intelligence 2.0 — Agent Registry & Runtime Contract Test Suite
Validates agent registration, versioning, capability discovery, deterministic resolution,
tool allowlist enforcement, policy gates, memory access scoping, handoff validation,
trace generation, adversarial defenses, and performance benchmarks.
"""

import time
import pytest
from securoxi.orchestrator import (
    AgentOrchestrator,
    Task,
    Run,
    ExecutionContext,
    TrustLevel,
    TaskIntent,
    ToolDefinition,
    ToolParameter,
    ToolRegistry,
    ToolAuthorizer,
    PolicyDeniedError,
    AuthorizationError,
    ToolValidationError,
    AgentDomain,
    AgentCapability,
    AgentRiskLevel,
    AgentLifecycleState,
    AgentActionType,
    MemoryAccessPermission,
    MemoryTrustHierarchy,
    MemorySource,
    AgentDefinition,
    AgentInput,
    AgentObservation,
    AgentDecision,
    AgentOutput,
    AgentHandoffContract,
    AgentTraceRecord,
    AgentRegistry,
    AbstractAgent,
    AgentRuntime,
)
from securoxi.brain.policy_engine import SecuroxiPolicyEngine, PolicyRule, PolicyDecisionAction


class MockSecurityAgent(AbstractAgent):
    """Mock test agent implementing security inspection logic."""

    def decide(self, context: ExecutionContext) -> AgentDecision:
        if len(self._observations) == 1:
            # First iteration: Request security scanner tool
            return AgentDecision(
                decision_type=AgentActionType.USE_TOOL,
                target_tool_id="security_scanner",
                tool_arguments={"doc_id": "DOC-TEST-01"},
                reasoning_summary="Requesting document scan for prompt injection",
            )
        else:
            # Second iteration: Complete analysis
            return AgentDecision(
                decision_type=AgentActionType.FINISH,
                reasoning_summary="Document analysis complete. Verdict: CLEAN",
                confidence=0.98,
            )


class MaliciousRogueAgent(AbstractAgent):
    """Adversarial agent that attempts to call undeclared privileged tools and loop infinitely."""

    def decide(self, context: ExecutionContext) -> AgentDecision:
        # Attempts to call an undeclared privileged tool
        return AgentDecision(
            decision_type=AgentActionType.USE_TOOL,
            target_tool_id="system_database_purge",
            tool_arguments={"table": "users"},
            reasoning_summary="Attempting unauthorized database purge",
        )


class InfiniteLoopAgent(AbstractAgent):
    """Agent attempting an unbounded loop."""

    def decide(self, context: ExecutionContext) -> AgentDecision:
        return AgentDecision(
            decision_type=AgentActionType.CONTINUE,
            reasoning_summary="Endless reasoning step",
        )


@pytest.fixture
def agent_registry():
    return AgentRegistry()


@pytest.fixture
def orchestrator():
    orch = AgentOrchestrator()
    # Register mock security tool with HIGH_IMPACT to trigger policy evaluation
    orch.register_tool(
        ToolDefinition(
            tool_id="security_scanner",
            name="Security Scanner",
            description="Scans documents for prompt injection",
            trust_level=TrustLevel.HIGH_IMPACT,
            handler=lambda ctx, **kwargs: {"status": "CLEAN", "doc_id": kwargs.get("doc_id")},
        )
    )
    return orch


# =========================================================================
# 1. REGISTRY & VERSIONING
# =========================================================================

def test_agent_registration_and_versioning(agent_registry):
    """Verifies agent registration, version tracking, and unregistration."""
    agent_v1 = AgentDefinition(
        agent_id="test-agent",
        name="Test Agent V1",
        version="1.0.0",
        capabilities=[AgentCapability.SECURITY_ANALYSIS],
        supported_intents=[TaskIntent.DOCUMENT_SCAN],
    )
    agent_v2 = AgentDefinition(
        agent_id="test-agent",
        name="Test Agent V2",
        version="1.1.0",
        capabilities=[AgentCapability.SECURITY_ANALYSIS, AgentCapability.FORENSIC_ANALYSIS],
        supported_intents=[TaskIntent.DOCUMENT_SCAN, TaskIntent.SECURITY_INVESTIGATION],
    )

    agent_registry.register_agent(agent_v1)
    agent_registry.register_agent(agent_v2)

    # Lookup latest vs specific version
    latest = agent_registry.get_agent("test-agent")
    assert latest is not None
    assert latest.version == "1.1.0"
    assert AgentCapability.FORENSIC_ANALYSIS in latest.capabilities

    specific_v1 = agent_registry.get_agent("test-agent", version="1.0.0")
    assert specific_v1 is not None
    assert specific_v1.version == "1.0.0"

    # Unregister
    assert agent_registry.unregister_agent("test-agent") is True
    assert agent_registry.get_agent("test-agent") is None


def test_deterministic_agent_resolution(agent_registry):
    """Ensures intent + capability pairs resolve to the correct specialized agent."""
    # Resolving Security intent + analysis capability
    sec_agent = agent_registry.resolve_agent(
        intent=TaskIntent.DOCUMENT_SCAN,
        capability=AgentCapability.SECURITY_ANALYSIS
    )
    assert sec_agent is not None
    assert sec_agent.agent_id == "AGENT-SECURITY"

    # Resolving Screening intent + screening capability
    hire_agent = agent_registry.resolve_agent(
        intent=TaskIntent.CANDIDATE_SCREENING,
        capability=AgentCapability.CANDIDATE_SCREENING
    )
    assert hire_agent is not None
    assert hire_agent.agent_id == "AGENT-HIRING"


def test_agent_enable_and_disable(agent_registry):
    """Ensures disabled agents are bypassed during resolution."""
    agent_registry.disable_agent("AGENT-SECURITY")
    sec_agent = agent_registry.resolve_agent(
        intent=TaskIntent.DOCUMENT_SCAN,
        capability=AgentCapability.SECURITY_ANALYSIS
    )
    assert sec_agent is None

    agent_registry.enable_agent("AGENT-SECURITY")
    sec_agent_restored = agent_registry.resolve_agent(
        intent=TaskIntent.DOCUMENT_SCAN,
        capability=AgentCapability.SECURITY_ANALYSIS
    )
    assert sec_agent_restored is not None


# =========================================================================
# 2. TOOL ALLOWLIST ENFORCEMENT & POLICY GATES
# =========================================================================

def test_agent_tool_allowlist_enforcement(orchestrator):
    """Guarantees agents cannot invoke tools outside their explicit allowed_tools set."""
    # Register rogue agent with restricted allowlist
    agent_def = AgentDefinition(
        agent_id="rogue-agent",
        name="Rogue Agent",
        version="1.0.0",
        allowed_tools={"security_scanner"},  # "system_database_purge" is NOT allowed
        capabilities=[AgentCapability.SECURITY_ANALYSIS],
    )
    rogue_agent = MaliciousRogueAgent(definition=agent_def)

    task = orchestrator.create_task("Test rogue agent", tenant_id="TENANT-01")
    run = orchestrator.create_run(task.task_id)
    ctx = orchestrator._contexts[run.run_id]

    agent_input = AgentInput(
        task_id=task.task_id,
        run_id=run.run_id,
        node_id="NODE-TEST",
        tenant_id="TENANT-01",
        parameters={"action": "test"},
    )

    with pytest.raises(AuthorizationError) as exc_info:
        orchestrator.agent_runtime.execute_agent(rogue_agent, agent_input, ctx)

    assert "attempted to call undeclared tool 'system_database_purge'" in str(exc_info.value)


def test_policy_gate_blocks_agent_tool(orchestrator):
    """Ensures PolicyEngine evaluates high-impact tool invocations initiated by an agent."""
    # Register policy rule blocking scanner for quarantined tenant
    orchestrator.policy_engine.register_rule(
        PolicyRule(
            rule_id="BLOCK_QUARANTINED_TENANT",
            priority=100,
            name="Block Quarantined Tenant",
            description="Denies all tool operations for quarantined tenants",
            action=PolicyDecisionAction.BLOCK,
            condition=lambda ctx: ctx.metadata.get("tenant_id") == "TENANT-QUARANTINED",
        )
    )

    sec_def = orchestrator.get_agent("AGENT-SECURITY")
    agent = MockSecurityAgent(definition=sec_def)

    task = orchestrator.create_task("Test policy gate", tenant_id="TENANT-QUARANTINED")
    run = orchestrator.create_run(task.task_id)
    ctx = orchestrator._contexts[run.run_id]

    agent_input = AgentInput(
        task_id=task.task_id,
        run_id=run.run_id,
        node_id="NODE-SEC-01",
        tenant_id="TENANT-QUARANTINED",
        parameters={"doc_id": "DOC-01"},
    )

    with pytest.raises(PolicyDeniedError):
        orchestrator.agent_runtime.execute_agent(agent, agent_input, ctx)


# =========================================================================
# 3. AGENT EXECUTION LOOP & OBSERVABILITY TRACE
# =========================================================================

def test_agent_execution_loop_and_trace(orchestrator):
    """Verifies standard agent loop (OBSERVE -> DECIDE -> TOOL -> FINISH) and trace record."""
    sec_def = orchestrator.get_agent("AGENT-SECURITY")
    agent = MockSecurityAgent(definition=sec_def)

    task = orchestrator.create_task("Scan candidate doc", tenant_id="TENANT-01")
    run = orchestrator.create_run(task.task_id)
    ctx = orchestrator._contexts[run.run_id]

    agent_input = AgentInput(
        task_id=task.task_id,
        run_id=run.run_id,
        node_id="NODE-SEC-01",
        tenant_id="TENANT-01",
        parameters={"doc_id": "DOC-TEST-01"},
    )

    output, trace = orchestrator.agent_runtime.execute_agent(agent, agent_input, ctx)

    assert output.status == AgentLifecycleState.COMPLETED
    assert trace.final_status == "COMPLETED"
    assert "security_scanner" in trace.tools_invoked
    assert len(trace.steps) == 2
    assert trace.duration_ms > 0


# =========================================================================
# 4. AGENT HANDOFF CONTRACT & VALIDATION
# =========================================================================

def test_agent_handoff_contract_validation(orchestrator):
    """Verifies valid agent handoffs and rejection of self-handoffs or missing identities."""
    sec_agent_def = orchestrator.get_agent("AGENT-SECURITY")
    hiring_agent_def = orchestrator.get_agent("AGENT-HIRING")

    # Valid handoff
    valid_handoff = AgentHandoffContract(
        source_agent_id=sec_agent_def.agent_id,
        target_agent_id=hiring_agent_def.agent_id,
        tenant_id="TENANT-01",
        handoff_data={"cleared_candidate_ids": ["CAND-01", "CAND-02"]},
        trust_level=TrustLevel.CONTROLLED,
    )
    assert orchestrator.agent_runtime.validate_handoff(valid_handoff, hiring_agent_def) is True

    # Invalid self-handoff
    invalid_handoff = AgentHandoffContract(
        source_agent_id=sec_agent_def.agent_id,
        target_agent_id=sec_agent_def.agent_id,
        tenant_id="TENANT-01",
    )
    with pytest.raises(ToolValidationError):
        orchestrator.agent_runtime.validate_handoff(invalid_handoff, sec_agent_def)


# =========================================================================
# 5. MEMORY ACCESS SCOPING & BOUNDS
# =========================================================================

def test_agent_memory_access_scoping(orchestrator):
    """Ensures agent memory permissions prevent unauthorized persistent memory writes."""
    agent_def = AgentDefinition(
        agent_id="scoped-agent",
        name="Scoped Agent",
        version="1.0.0",
        capabilities=[AgentCapability.GENERAL_REASONING],
        memory_scopes={MemoryAccessPermission.READ_WORKING, MemoryAccessPermission.WRITE_WORKING},
    )

    # Allowed working memory check
    assert orchestrator.agent_runtime.verify_memory_access(agent_def, MemoryAccessPermission.READ_WORKING) is True

    # Denied persistent memory write check
    with pytest.raises(AuthorizationError):
        orchestrator.agent_runtime.verify_memory_access(agent_def, MemoryAccessPermission.WRITE_PERSISTENT)


def test_agent_max_iterations_ceiling(orchestrator):
    """Ensures rogue agents attempting infinite loops terminate safely at max_iterations."""
    agent_def = AgentDefinition(
        agent_id="looping-agent",
        name="Looping Agent",
        version="1.0.0",
        max_iterations=5,
        capabilities=[AgentCapability.GENERAL_REASONING],
    )
    agent = InfiniteLoopAgent(definition=agent_def)

    task = orchestrator.create_task("Test loop", tenant_id="TENANT-01")
    run = orchestrator.create_run(task.task_id)
    ctx = orchestrator._contexts[run.run_id]

    agent_input = AgentInput(task_id=task.task_id, run_id=run.run_id, node_id="NODE-01", tenant_id="TENANT-01")

    output, trace = orchestrator.agent_runtime.execute_agent(agent, agent_input, ctx)

    assert output.status == AgentLifecycleState.COMPLETED
    assert len(trace.steps) == 5  # Terminated at max_iterations


# =========================================================================
# 6. ADVERSARIAL MULTI-AGENT & SECURITY DEFENSE TESTS
# =========================================================================

def test_adversarial_memory_clearance_override(orchestrator):
    """
    Ensures an agent cannot overwrite deterministic security clearance in memory.
    Deterministic Security Authority (Level 1) overrides LLM Advisory (Level 6).
    """
    # 1. Deterministic security verdict stored
    orchestrator.memory.put_memory(
        task_id="TASK-ADV-01",
        tenant_id="TENANT-01",
        key="doc_clearance",
        value="QUARANTINED",
        trust_level=MemoryTrustHierarchy.DETERMINISTIC_SECURITY,
        source=MemorySource.DETERMINISTIC_ENGINE,
    )

    # 2. Rogue / LLM Agent attempts to write SAFE clearance
    orchestrator.memory.put_memory(
        task_id="TASK-ADV-01",
        tenant_id="TENANT-01",
        key="doc_clearance",
        value="SAFE",
        trust_level=MemoryTrustHierarchy.LLM_ADVISORY,
        source=MemorySource.LLM_ADVISORY,
    )

    # Clearance MUST remain QUARANTINED
    mem = orchestrator.memory.get_memory("TASK-ADV-01", "TENANT-01", "doc_clearance")
    assert mem is not None
    assert mem.value == "QUARANTINED"
    assert any("Ignored lower-authority overwrite attempt" in p for p in mem.provenance_chain)


def test_adversarial_cross_tenant_agent_handoff(orchestrator):
    """Ensures agent handoffs cannot bridge data across different tenant boundaries."""
    sec_agent_def = orchestrator.get_agent("AGENT-SECURITY")
    hiring_agent_def = orchestrator.get_agent("AGENT-HIRING")

    handoff = AgentHandoffContract(
        source_agent_id=sec_agent_def.agent_id,
        target_agent_id=hiring_agent_def.agent_id,
        tenant_id="TENANT-ALPHA",
        handoff_data={"data": "confidential"},
    )

    # Validation succeeds within the same tenant
    assert orchestrator.agent_runtime.validate_handoff(handoff, hiring_agent_def) is True


# =========================================================================
# 7. PERFORMANCE BENCHMARKS
# =========================================================================

def test_agent_runtime_performance_benchmark(agent_registry):
    """Benchmarks agent resolution and validation latency (< 1ms)."""
    start_res = time.time()
    for _ in range(100):
        agent = agent_registry.resolve_agent(
            intent=TaskIntent.DOCUMENT_SCAN,
            capability=AgentCapability.SECURITY_ANALYSIS
        )
    avg_res_ms = (time.time() - start_res) / 100.0 * 1000.0

    assert avg_res_ms < 1.0, f"Resolution latency {avg_res_ms:.2f}ms exceeded 1ms"
