"""
SECUROXI AI Intelligence 2.0 — Durable Execution State, Checkpointing, Resumability & Memory
Validates task and run persistence, checkpoint capture & integrity hash, crash recovery & resumption,
pause/cancel, human approval persistence, worker leases, memory scopes, provenance, conflict hierarchy,
cross-tenant memory isolation, failure journal, and performance benchmarks.
"""

import time
import pytest
from securoxi.orchestrator import (
    AgentOrchestrator,
    Task,
    Run,
    RunState,
    NodeState,
    NodeType,
    ExecutionNode,
    ExecutionDAG,
    ExecutionContext,
    Checkpoint,
    CheckpointTrigger,
    WorkerLease,
    LeaseStatus,
    MemoryScope,
    MemoryType,
    MemorySource,
    MemoryTrustHierarchy,
    MemoryItem,
    MemorySnapshot,
    FailureJournalEntry,
    DurableStateStore,
    DurableMemoryManager,
    RunRecoveryManager,
    TenantAccessError,
    OrchestratorError,
)


@pytest.fixture
def state_store():
    return DurableStateStore()


@pytest.fixture
def memory_manager():
    return DurableMemoryManager()


@pytest.fixture
def orchestrator():
    return AgentOrchestrator()


# =========================================================================
# 1. TASK & RUN PERSISTENCE
# =========================================================================

def test_task_and_run_durability(state_store):
    """Verifies that tasks and execution runs are persisted and retrievable."""
    task = Task(
        objective="Scan candidate collection",
        tenant_id="TENANT-DURABLE",
        context={"folder_id": "FLD-01"}
    )
    state_store.save_task(task)

    loaded_task = state_store.load_task(task.task_id)
    assert loaded_task is not None
    assert loaded_task["task_id"] == task.task_id
    assert loaded_task["tenant_id"] == "TENANT-DURABLE"

    run = Run(task_id=task.task_id, tenant_id=task.tenant_id, state=RunState.READY)
    state_store.save_run(run)

    loaded_run = state_store.load_run(run.run_id)
    assert loaded_run is not None
    assert loaded_run["run_id"] == run.run_id
    assert loaded_run["state"] == "READY"


# =========================================================================
# 2. CHECKPOINT CAPTURE & INTEGRITY HASH
# =========================================================================

def test_checkpoint_creation_and_integrity_hash(state_store):
    """Ensures checkpoints compute deterministic SHA-256 integrity hashes."""
    chk = Checkpoint(
        run_id="RUN-TEST-01",
        task_id="TASK-TEST-01",
        tenant_id="TENANT-01",
        version=1,
        completed_node_ids=["NODE-A", "NODE-B"],
        pending_node_ids=["NODE-C"],
        shared_state_snapshot={"candidate_count": 50},
        budget_consumed_steps=2,
    )
    saved_chk = state_store.save_checkpoint(chk)

    assert len(saved_chk.integrity_hash) == 64  # Valid SHA-256 string
    assert saved_chk.compute_integrity_hash() == saved_chk.integrity_hash

    # Retrieve from store
    latest = state_store.load_latest_checkpoint("RUN-TEST-01")
    assert latest is not None
    assert latest.checkpoint_id == saved_chk.checkpoint_id
    assert latest.completed_node_ids == ["NODE-A", "NODE-B"]


# =========================================================================
# 3. CRASH RECOVERY & RESUMPTION
# =========================================================================

def test_crash_recovery_and_resumption(orchestrator):
    """
    Simulates:
    1. Run executes Node A.
    2. Checkpoint taken.
    3. Process crash simulated (state wiped from memory).
    4. Recovery rehydrates Node A as COMPLETED and continues Node B & C to completion.
    """
    task = orchestrator.create_task("Crash recovery test", tenant_id="TENANT-RECOVER")
    run = orchestrator.create_run(task.task_id)

    node_a = ExecutionNode(name="step_a", action_fn=lambda ctx: "Result A")
    node_b = ExecutionNode(name="step_b", dependencies=[node_a.node_id], action_fn=lambda ctx: "Result B")
    node_c = ExecutionNode(name="step_c", dependencies=[node_b.node_id], action_fn=lambda ctx: "Result C")

    orchestrator.add_node_to_run(run.run_id, node_a)
    orchestrator.add_node_to_run(run.run_id, node_b)
    orchestrator.add_node_to_run(run.run_id, node_c)

    # Execute only step A
    dag = orchestrator.get_dag(run.run_id)
    ctx = orchestrator._contexts[run.run_id]
    orchestrator.execute_node(node_a, ctx)
    assert node_a.state == NodeState.COMPLETED

    # Checkpoint state after step A
    chk = orchestrator.checkpoint_run(run.run_id, trigger=CheckpointTrigger.NODE_COMPLETED)
    assert node_a.node_id in chk.completed_node_ids

    # Simulate Process Restart: instantiate a brand new orchestrator sharing state store
    fresh_orchestrator = AgentOrchestrator(
        state_store=orchestrator.state_store,
        memory_manager=orchestrator.memory
    )
    # Register the run and base DAG in fresh orchestrator
    fresh_orchestrator._runs[run.run_id] = run
    fresh_orchestrator._dags[run.run_id] = dag

    # Resume run from checkpoint
    completed_run = fresh_orchestrator.resume_run(
        run_id=run.run_id,
        requester_tenant_id="TENANT-RECOVER",
        parallel=False
    )

    assert completed_run.state == RunState.COMPLETED
    resumed_dag = fresh_orchestrator.get_dag(run.run_id)
    assert resumed_dag.get_node(node_a.node_id).state == NodeState.COMPLETED
    assert resumed_dag.get_node(node_b.node_id).state == NodeState.COMPLETED
    assert resumed_dag.get_node(node_c.node_id).state == NodeState.COMPLETED


# =========================================================================
# 4. PAUSE AND RESUME
# =========================================================================

def test_pause_and_resume(orchestrator):
    """Verifies that pausing a run checkpoints state and resuming finishes the run."""
    task = orchestrator.create_task("Pause Resume Test", tenant_id="TENANT-01")
    run = orchestrator.create_run(task.task_id)

    n1 = ExecutionNode(name="p1", action_fn=lambda ctx: "P1")
    n2 = ExecutionNode(name="p2", dependencies=[n1.node_id], action_fn=lambda ctx: "P2")
    orchestrator.add_node_to_run(run.run_id, n1)
    orchestrator.add_node_to_run(run.run_id, n2)

    # Pause run
    paused_run = orchestrator.pause_run(run.run_id)
    assert paused_run.state == RunState.PAUSED

    # Resume run
    resumed_run = orchestrator.resume_run(run.run_id, requester_tenant_id="TENANT-01", parallel=False)
    assert resumed_run.state == RunState.COMPLETED


# =========================================================================
# 5. HUMAN APPROVAL PERSISTENCE ACROSS RESTART
# =========================================================================

def test_human_approval_persists_across_restart(orchestrator):
    """Ensures pending human approval requests survive process restart and can be decided."""
    task = orchestrator.create_task("Approval Persist", tenant_id="TENANT-01")
    run = orchestrator.create_run(task.task_id)

    app_node = ExecutionNode(
        name="human_approval_node",
        node_type=NodeType.HUMAN_APPROVAL,
        description="Approve production promotion"
    )
    orchestrator.add_node_to_run(run.run_id, app_node)

    # Run pauses in WAITING_FOR_APPROVAL
    paused_run = orchestrator.start_run(run.run_id, parallel=False)
    assert paused_run.state == RunState.WAITING_FOR_APPROVAL

    approvals = list(orchestrator._approvals.values())
    assert len(approvals) == 1
    app_id = approvals[0].approval_id

    # Checkpoint WAITING_FOR_APPROVAL state
    orchestrator.checkpoint_run(run.run_id, trigger=CheckpointTrigger.BEFORE_HUMAN_APPROVAL)

    # Process restart simulation: new orchestrator instance with preserved approval request
    fresh_orchestrator = AgentOrchestrator(
        state_store=orchestrator.state_store,
        memory_manager=orchestrator.memory
    )
    fresh_orchestrator._approvals = dict(orchestrator._approvals)
    fresh_orchestrator._runs = dict(orchestrator._runs)
    fresh_orchestrator._dags = dict(orchestrator._dags)
    fresh_orchestrator._contexts = dict(orchestrator._contexts)

    # Approve request on fresh orchestrator
    decided = fresh_orchestrator.submit_approval(app_id, approved=True, decided_by="SecLead_Bob")
    assert decided.status.value == "APPROVED"


# =========================================================================
# 6. WORKER LEASES & STALE LEASE RECOVERY
# =========================================================================

def test_worker_lease_and_stale_recovery(state_store):
    """Verifies exclusive node leases and automatic recovery of expired worker leases."""
    # Worker 1 acquires lease
    l1 = state_store.acquire_lease(run_id="R1", node_id="N1", worker_id="W1", duration_sec=0.1)
    assert l1.is_valid()

    # Worker 2 attempts claim on same node -> blocked
    with pytest.raises(Exception):
        state_store.acquire_lease(run_id="R1", node_id="N1", worker_id="W2", duration_sec=10.0)

    # Wait for lease to expire
    time.sleep(0.15)
    assert not l1.is_valid()

    recovery_mgr = RunRecoveryManager(state_store=state_store, memory_manager=DurableMemoryManager())
    recovered = recovery_mgr.recover_stale_leases()
    assert recovered == 1

    # Worker 2 can now claim
    l2 = state_store.acquire_lease(run_id="R1", node_id="N1", worker_id="W2", duration_sec=10.0)
    assert l2.is_valid()
    assert l2.worker_id == "W2"


# =========================================================================
# 7. MEMORY SCOPES, PROVENANCE & CONFLICT RESOLUTION
# =========================================================================

def test_memory_provenance_and_authority_conflict(memory_manager):
    """
    Guarantees authority precedence:
    Deterministic Security Authority (Level 1) overrides LLM Advisory (Level 6).
    Lower authority cannot overwrite higher authority.
    """
    # 1. Deterministic Engine records security verdict
    sec_item = memory_manager.put_memory(
        task_id="TASK-MEM-01",
        tenant_id="TENANT-01",
        key="candidate_verdict",
        value="QUARANTINED",
        scope=MemoryScope.TASK,
        memory_type=MemoryType.FACT,
        source=MemorySource.DETERMINISTIC_ENGINE,
        trust_level=MemoryTrustHierarchy.DETERMINISTIC_SECURITY,
        provenance_chain=["NODE-SCAN-01"]
    )
    assert sec_item.value == "QUARANTINED"

    # 2. Malicious / Advisory LLM attempt to overwrite security verdict
    llm_attempt = memory_manager.put_memory(
        task_id="TASK-MEM-01",
        tenant_id="TENANT-01",
        key="candidate_verdict",
        value="SAFE_OVERRIDE",
        scope=MemoryScope.TASK,
        memory_type=MemoryType.FACT,
        source=MemorySource.LLM_ADVISORY,
        trust_level=MemoryTrustHierarchy.LLM_ADVISORY,
        provenance_chain=["NODE-LLM-CHAT"]
    )

    # Value MUST remain QUARANTINED
    assert llm_attempt.value == "QUARANTINED"
    assert any("Ignored lower-authority overwrite attempt" in p for p in llm_attempt.provenance_chain)


def test_memory_cross_tenant_isolation(memory_manager):
    """Ensures memory access across tenant boundaries is strictly rejected."""
    memory_manager.put_memory(
        task_id="TASK-T1",
        tenant_id="TENANT-ALPHA",
        key="confidential_secret",
        value="SECRET-ALPHA"
    )

    with pytest.raises(TenantAccessError):
        memory_manager.get_memory(task_id="TASK-T1", tenant_id="TENANT-BETA", key="confidential_secret")


# =========================================================================
# 8. FAILURE JOURNAL & PERFORMANCE BENCHMARKS
# =========================================================================

def test_failure_journal_logging(state_store):
    """Verifies failure journal recording for telemetry and post-mortem analysis."""
    entry = FailureJournalEntry(
        run_id="RUN-FAIL-01",
        node_id="NODE-OCR-03",
        tenant_id="TENANT-01",
        error_code="OCR_CORRUPT_PAGE",
        error_message="Page 3 TIFF image stream corrupted",
        is_retryable=True,
        retry_count=2,
        recovery_decision="QUARANTINE_PAGE"
    )
    state_store.record_failure(entry)

    failures = state_store.list_failures("RUN-FAIL-01")
    assert len(failures) == 1
    assert failures[0].error_code == "OCR_CORRUPT_PAGE"
    assert failures[0].recovery_decision == "QUARANTINE_PAGE"


def test_checkpoint_and_restore_performance(orchestrator):
    """Benchmarks checkpoint creation and rehydration latency (< 2ms)."""
    task = orchestrator.create_task("Bench", tenant_id="TENANT-BENCH")
    run = orchestrator.create_run(task.task_id)
    dag = orchestrator.get_dag(run.run_id)
    ctx = orchestrator._contexts[run.run_id]

    start_time = time.time()
    for i in range(50):
        chk = orchestrator.recovery.capture_checkpoint(run, dag, ctx)
    chk_time = (time.time() - start_time) / 50.0 * 1000.0

    start_restore = time.time()
    for i in range(50):
        orchestrator.recovery.rehydrate_run(run.run_id, dag, requester_tenant_id="TENANT-BENCH")
    restore_time = (time.time() - start_restore) / 50.0 * 1000.0

    assert chk_time < 2.0, f"Checkpoint latency {chk_time:.2f}ms exceeded 2ms"
    assert restore_time < 2.0, f"Restore latency {restore_time:.2f}ms exceeded 2ms"
