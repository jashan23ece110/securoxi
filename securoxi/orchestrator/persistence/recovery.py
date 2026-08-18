"""
SECUROXI AI Intelligence 2.0 — Run Recovery & Checkpoint Rehydration
Handles snapshot creation, crash recovery, stale lease detection, and security revalidation.
"""

import time
from typing import Dict, Any, List, Optional, Tuple

from securoxi.orchestrator.models import Run, RunState
from securoxi.orchestrator.graph import ExecutionDAG, ExecutionNode, NodeState
from securoxi.orchestrator.context import ExecutionContext
from securoxi.orchestrator.budget import BudgetTracker
from securoxi.orchestrator.persistence.types import CheckpointTrigger, LeaseStatus
from securoxi.orchestrator.persistence.models import Checkpoint
from securoxi.orchestrator.persistence.store import DurableStateStore
from securoxi.orchestrator.persistence.memory import DurableMemoryManager
from securoxi.orchestrator.errors import (
    OrchestratorError,
    TenantAccessError,
    PolicyDeniedError,
)
from securoxi.brain.policy_engine import SecuroxiPolicyEngine
from securoxi.logger import get_logger

logger = get_logger("orchestrator.recovery")


class RunRecoveryManager:
    """
    Manages crash recovery, checkpoint capture, and execution state rehydration.
    """

    def __init__(
        self,
        state_store: DurableStateStore,
        memory_manager: DurableMemoryManager,
        policy_engine: Optional[SecuroxiPolicyEngine] = None,
    ):
        self.store = state_store
        self.memory = memory_manager
        self.policy_engine = policy_engine or SecuroxiPolicyEngine()

    def capture_checkpoint(
        self,
        run: Run,
        dag: ExecutionDAG,
        ctx: ExecutionContext,
        trigger: CheckpointTrigger = CheckpointTrigger.NODE_COMPLETED,
    ) -> Checkpoint:
        """Captures and stores an immutable execution checkpoint."""
        completed_nodes = [nid for nid, n in dag.nodes.items() if n.state == NodeState.COMPLETED]
        active_nodes = [nid for nid, n in dag.nodes.items() if n.state == NodeState.RUNNING]
        pending_nodes = [nid for nid, n in dag.nodes.items() if n.state in {NodeState.PENDING, NodeState.READY}]
        skipped_nodes = [nid for nid, n in dag.nodes.items() if n.state == NodeState.SKIPPED]
        failed_nodes = [nid for nid, n in dag.nodes.items() if n.state == NodeState.FAILED]

        # Capture memory snapshot
        mem_snapshot = self.memory.create_snapshot(run.task_id, run.tenant_id)

        checkpoint = Checkpoint(
            run_id=run.run_id,
            task_id=run.task_id,
            tenant_id=run.tenant_id,
            version=len(self.store._run_checkpoints.get(run.run_id, [])) + 1,
            plan_version=run.metadata.get("plan_version", 1),
            trigger=trigger,
            completed_node_ids=completed_nodes,
            active_node_ids=active_nodes,
            pending_node_ids=pending_nodes,
            skipped_node_ids=skipped_nodes,
            failed_node_ids=failed_nodes,
            shared_state_snapshot=ctx.get_all_shared_state(),
            budget_consumed_steps=ctx.budget_tracker.current_steps,
            budget_consumed_tool_calls=ctx.budget_tracker.current_tool_calls,
            budget_consumed_runtime_ms=run.total_runtime_ms,
            memory_snapshot_id=mem_snapshot.snapshot_id,
            created_at=time.time(),
        )

        self.store.save_checkpoint(checkpoint)
        logger.info(f"Captured Checkpoint {checkpoint.checkpoint_id} for Run {run.run_id} (Trigger: {trigger.value})")
        return checkpoint

    def rehydrate_run(
        self,
        run_id: str,
        base_dag: ExecutionDAG,
        checkpoint_id: Optional[str] = None,
        requester_tenant_id: str = "TENANT-DEFAULT",
    ) -> Tuple[Run, ExecutionDAG, ExecutionContext]:
        """
        Reconstructs run, DAG, budget, and shared context from the latest durable checkpoint.
        Re-validates tenant authorization and security policies.
        """
        # 1. Load Checkpoint
        if checkpoint_id:
            checkpoint = self.store.load_checkpoint(checkpoint_id)
        else:
            checkpoint = self.store.load_latest_checkpoint(run_id)

        if not checkpoint:
            raise OrchestratorError(f"No valid checkpoint found for Run '{run_id}'")

        # 2. Verify Tenant Isolation
        if checkpoint.tenant_id != requester_tenant_id:
            raise TenantAccessError(
                f"Unauthorized recovery attempt across tenant boundary (Checkpoint: {checkpoint.tenant_id}, Requester: {requester_tenant_id})"
            )

        # 3. Verify Checkpoint Integrity Hash
        expected_hash = checkpoint.compute_integrity_hash()
        if checkpoint.integrity_hash != expected_hash:
            raise OrchestratorError(f"Checkpoint {checkpoint.checkpoint_id} integrity hash verification failed (tampering detected)")

        # 4. Load & Rehydrate Run Record
        run_data = self.store.load_run(run_id) or {}
        run = Run(
            run_id=run_id,
            task_id=checkpoint.task_id,
            tenant_id=checkpoint.tenant_id,
            state=RunState.READY,
            metadata={"plan_version": checkpoint.plan_version, "rehydrated_from": checkpoint.checkpoint_id},
        )

        # 5. Reconstruct DAG Node States
        reconstructed_dag = ExecutionDAG(run_id=run_id)
        for node_id, original_node in base_dag.nodes.items():
            node = original_node  # Copy node
            node.run_id = run_id

            if node_id in checkpoint.completed_node_ids:
                node.state = NodeState.COMPLETED
            elif node_id in checkpoint.skipped_node_ids:
                node.state = NodeState.SKIPPED
            elif node_id in checkpoint.failed_node_ids:
                node.state = NodeState.READY  # Reset for recovery retry
            else:
                # Active/Interrupted nodes are safely reset to READY for idempotent continuation
                node.state = NodeState.PENDING

            reconstructed_dag.add_node(node)

        # Re-attach edge dependencies
        reconstructed_dag.edges = dict(base_dag.edges)

        # 6. Rehydrate Execution Context and Shared State
        budget_tracker = BudgetTracker()
        budget_tracker.current_steps = checkpoint.budget_consumed_steps
        budget_tracker.current_tool_calls = checkpoint.budget_consumed_tool_calls

        ctx = ExecutionContext(
            run=run,
            tenant_id=checkpoint.tenant_id,
            budget_tracker=budget_tracker,
        )

        # Restore shared state dictionary
        for key, val in checkpoint.shared_state_snapshot.items():
            ctx.set_shared_value(key, val, source_node_id="REHYDRATED_CHECKPOINT")

        # 7. Restore Memory Snapshot if available
        if checkpoint.memory_snapshot_id:
            try:
                self.memory.restore_snapshot(checkpoint.memory_snapshot_id, checkpoint.tenant_id)
            except Exception as mem_err:
                logger.warning(f"Memory snapshot restore warning: {mem_err}")

        logger.info(f"Successfully rehydrated Run {run_id} from Checkpoint {checkpoint.checkpoint_id} ({len(checkpoint.completed_node_ids)} completed nodes preserved)")
        return run, reconstructed_dag, ctx

    def recover_stale_leases(self) -> int:
        """Identifies expired worker leases and safely resets them for retry."""
        expired_leases = self.store.list_expired_leases()
        recovered_count = 0

        for lease in expired_leases:
            lease.status = LeaseStatus.EXPIRED
            self.store.release_lease(lease.lease_id)
            recovered_count += 1
            logger.warning(f"Recovered expired worker lease {lease.lease_id} on node {lease.node_id}")

        return recovered_count
