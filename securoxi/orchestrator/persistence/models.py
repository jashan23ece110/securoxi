"""
SECUROXI AI Intelligence 2.0 — Persistence Data Models
Defines strongly typed records for Checkpoints, Memory Items, Memory Snapshots,
Worker Leases, and Failure Journal entries.
"""

import time
import uuid
import hashlib
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from securoxi.orchestrator.persistence.types import (
    MemoryScope,
    MemoryType,
    MemorySource,
    MemoryTrustHierarchy,
    CheckpointTrigger,
    LeaseStatus,
)


@dataclass
class MemoryItem:
    """A strongly typed unit of working or task memory with provenance and authority ranking."""
    memory_id: str = field(default_factory=lambda: f"MEM-{uuid.uuid4().hex[:8].upper()}")
    task_id: str = ""
    tenant_id: str = "TENANT-DEFAULT"
    scope: MemoryScope = MemoryScope.WORKING
    memory_type: MemoryType = MemoryType.FACT
    source: MemorySource = MemorySource.DETERMINISTIC_ENGINE
    trust_level: MemoryTrustHierarchy = MemoryTrustHierarchy.DETERMINISTIC_SECURITY
    key: str = ""
    value: Any = None
    provenance_chain: List[str] = field(default_factory=list)  # list of source node IDs / tool names
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "task_id": self.task_id,
            "tenant_id": self.tenant_id,
            "scope": self.scope.value,
            "memory_type": self.memory_type.value,
            "source": self.source.value,
            "trust_level": self.trust_level.value,
            "key": self.key,
            "value": self.value,
            "provenance_chain": self.provenance_chain,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        return cls(
            memory_id=data.get("memory_id", ""),
            task_id=data.get("task_id", ""),
            tenant_id=data.get("tenant_id", "TENANT-DEFAULT"),
            scope=MemoryScope(data.get("scope", MemoryScope.WORKING.value)),
            memory_type=MemoryType(data.get("memory_type", MemoryType.FACT.value)),
            source=MemorySource(data.get("source", MemorySource.DETERMINISTIC_ENGINE.value)),
            trust_level=MemoryTrustHierarchy(data.get("trust_level", MemoryTrustHierarchy.DETERMINISTIC_SECURITY.value)),
            key=data.get("key", ""),
            value=data.get("value"),
            provenance_chain=data.get("provenance_chain", []),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )


@dataclass
class MemorySnapshot:
    """A complete immutable capture of task memory at a specific checkpoint."""
    snapshot_id: str = field(default_factory=lambda: f"MSNAP-{uuid.uuid4().hex[:8].upper()}")
    task_id: str = ""
    tenant_id: str = "TENANT-DEFAULT"
    items: List[MemoryItem] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "task_id": self.task_id,
            "tenant_id": self.tenant_id,
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at,
        }


@dataclass
class Checkpoint:
    """Durable state checkpoint enabling safe crash recovery and resumption."""
    checkpoint_id: str = field(default_factory=lambda: f"CHK-{uuid.uuid4().hex[:10].upper()}")
    run_id: str = ""
    task_id: str = ""
    tenant_id: str = "TENANT-DEFAULT"
    version: int = 1
    plan_version: int = 1
    trigger: CheckpointTrigger = CheckpointTrigger.NODE_COMPLETED
    completed_node_ids: List[str] = field(default_factory=list)
    active_node_ids: List[str] = field(default_factory=list)
    pending_node_ids: List[str] = field(default_factory=list)
    skipped_node_ids: List[str] = field(default_factory=list)
    failed_node_ids: List[str] = field(default_factory=list)
    shared_state_snapshot: Dict[str, Any] = field(default_factory=dict)
    budget_consumed_steps: int = 0
    budget_consumed_tool_calls: int = 0
    budget_consumed_runtime_ms: float = 0.0
    memory_snapshot_id: Optional[str] = None
    integrity_hash: str = ""
    created_at: float = field(default_factory=time.time)

    def compute_integrity_hash(self) -> str:
        """Computes a deterministic SHA-256 integrity hash across checkpoint state."""
        payload = {
            "checkpoint_id": self.checkpoint_id,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "tenant_id": self.tenant_id,
            "version": self.version,
            "plan_version": self.plan_version,
            "completed": sorted(self.completed_node_ids),
            "pending": sorted(self.pending_node_ids),
            "shared_state": self.shared_state_snapshot,
            "budget_steps": self.budget_consumed_steps,
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        if not self.integrity_hash:
            self.integrity_hash = self.compute_integrity_hash()
        return {
            "checkpoint_id": self.checkpoint_id,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "tenant_id": self.tenant_id,
            "version": self.version,
            "plan_version": self.plan_version,
            "trigger": self.trigger.value,
            "completed_node_ids": self.completed_node_ids,
            "active_node_ids": self.active_node_ids,
            "pending_node_ids": self.pending_node_ids,
            "skipped_node_ids": self.skipped_node_ids,
            "failed_node_ids": self.failed_node_ids,
            "shared_state_snapshot": self.shared_state_snapshot,
            "budget_consumed_steps": self.budget_consumed_steps,
            "budget_consumed_tool_calls": self.budget_consumed_tool_calls,
            "budget_consumed_runtime_ms": self.budget_consumed_runtime_ms,
            "memory_snapshot_id": self.memory_snapshot_id,
            "integrity_hash": self.integrity_hash,
            "created_at": self.created_at,
        }


@dataclass
class WorkerLease:
    """A distributed worker lease preventing duplicate execution of side effects."""
    lease_id: str = field(default_factory=lambda: f"LEASE-{uuid.uuid4().hex[:8].upper()}")
    run_id: str = ""
    node_id: str = ""
    worker_id: str = ""
    status: LeaseStatus = LeaseStatus.ACTIVE
    lease_duration_sec: float = 60.0
    acquired_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 60.0)
    last_heartbeat: float = field(default_factory=time.time)

    def is_valid(self) -> bool:
        return self.status == LeaseStatus.ACTIVE and time.time() < self.expires_at

    def heartbeat(self, extend_sec: Optional[float] = None):
        now = time.time()
        self.last_heartbeat = now
        duration = extend_sec or self.lease_duration_sec
        self.expires_at = now + duration

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lease_id": self.lease_id,
            "run_id": self.run_id,
            "node_id": self.node_id,
            "worker_id": self.worker_id,
            "status": self.status.value,
            "acquired_at": self.acquired_at,
            "expires_at": self.expires_at,
            "last_heartbeat": self.last_heartbeat,
        }


@dataclass
class FailureJournalEntry:
    """Structured audit record of node failures for recovery and telemetry."""
    failure_id: str = field(default_factory=lambda: f"FAIL-{uuid.uuid4().hex[:8].upper()}")
    run_id: str = ""
    node_id: str = ""
    tenant_id: str = "TENANT-DEFAULT"
    error_code: str = "UNKNOWN_ERROR"
    error_message: str = ""
    is_retryable: bool = False
    retry_count: int = 0
    last_known_state: str = "RUNNING"
    recovery_decision: str = "RETRY"  # "RETRY", "QUARANTINE", "FAIL_NODE", "REPLAN"
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "failure_id": self.failure_id,
            "run_id": self.run_id,
            "node_id": self.node_id,
            "tenant_id": self.tenant_id,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "is_retryable": self.is_retryable,
            "retry_count": self.retry_count,
            "last_known_state": self.last_known_state,
            "recovery_decision": self.recovery_decision,
            "created_at": self.created_at,
        }
