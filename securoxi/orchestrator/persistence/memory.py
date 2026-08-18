"""
SECUROXI AI Intelligence 2.0 — Durable Memory Manager
Provides multi-scoped working and task memory with strict provenance tracking,
authority-based conflict resolution, snapshotting, and rehydration.
"""

import time
import threading
from typing import Dict, Any, List, Optional, Tuple

from securoxi.orchestrator.persistence.types import (
    MemoryScope,
    MemoryType,
    MemorySource,
    MemoryTrustHierarchy,
)
from securoxi.orchestrator.persistence.models import (
    MemoryItem,
    MemorySnapshot,
)
from securoxi.orchestrator.errors import TenantAccessError, PolicyDeniedError


class DurableMemoryManager:
    """
    Thread-safe, multi-tenant memory management engine.
    Guarantees authority precedence during conflicts and maintains complete provenance chains.
    """

    def __init__(self):
        # (task_id, tenant_id, key) -> MemoryItem
        self._memory_store: Dict[Tuple[str, str, str], MemoryItem] = {}
        self._snapshots: Dict[str, MemorySnapshot] = {}
        self._lock = threading.RLock()

    def put_memory(
        self,
        task_id: str,
        tenant_id: str,
        key: str,
        value: Any,
        scope: MemoryScope = MemoryScope.WORKING,
        memory_type: MemoryType = MemoryType.FACT,
        source: MemorySource = MemorySource.DETERMINISTIC_ENGINE,
        trust_level: MemoryTrustHierarchy = MemoryTrustHierarchy.DETERMINISTIC_SECURITY,
        provenance_chain: Optional[List[str]] = None,
    ) -> MemoryItem:
        """
        Stores or updates a memory item. Enforces deterministic conflict resolution
        where higher authority sources supersede lower authority sources.
        """
        with self._lock:
            store_key = (task_id, tenant_id, key)
            existing_item = self._memory_store.get(store_key)

            new_item = MemoryItem(
                task_id=task_id,
                tenant_id=tenant_id,
                scope=scope,
                memory_type=memory_type,
                source=source,
                trust_level=trust_level,
                key=key,
                value=value,
                provenance_chain=provenance_chain or [],
                created_at=time.time(),
                updated_at=time.time(),
            )

            if existing_item:
                resolved_item = self._resolve_conflict(existing_item, new_item)
                self._memory_store[store_key] = resolved_item
                return resolved_item
            else:
                self._memory_store[store_key] = new_item
                return new_item

    def get_memory(
        self,
        task_id: str,
        tenant_id: str,
        key: str,
        scope: Optional[MemoryScope] = None
    ) -> Optional[MemoryItem]:
        """Retrieves a typed memory item with tenant isolation enforcement."""
        with self._lock:
            # Check if this task_id has memory registered under a different tenant
            for (t_id, other_ten_id, k), item in self._memory_store.items():
                if t_id == task_id and k == key and other_ten_id != tenant_id:
                    raise TenantAccessError(
                        f"Unauthorized cross-tenant memory access: Item '{key}' belongs to tenant '{other_ten_id}', requested by '{tenant_id}'"
                    )

            store_key = (task_id, tenant_id, key)
            item = self._memory_store.get(store_key)
            if item:
                if scope and item.scope != scope:
                    return None
                return item
            return None

    def list_memory(
        self,
        task_id: str,
        tenant_id: str,
        scope: Optional[MemoryScope] = None
    ) -> List[MemoryItem]:
        """Lists all memory items for a specific task and tenant."""
        with self._lock:
            results = []
            for (t_id, ten_id, _), item in self._memory_store.items():
                if t_id == task_id and ten_id == tenant_id:
                    if scope is None or item.scope == scope:
                        results.append(item)
            return results

    def delete_memory(self, task_id: str, tenant_id: str, key: str) -> bool:
        """Deletes a memory entry."""
        with self._lock:
            store_key = (task_id, tenant_id, key)
            if store_key in self._memory_store:
                del self._memory_store[store_key]
                return True
            return False

    def create_snapshot(self, task_id: str, tenant_id: str) -> MemorySnapshot:
        """Creates an immutable snapshot of all task and working memory."""
        with self._lock:
            items = self.list_memory(task_id, tenant_id)
            snapshot = MemorySnapshot(
                task_id=task_id,
                tenant_id=tenant_id,
                items=items,
                created_at=time.time()
            )
            self._snapshots[snapshot.snapshot_id] = snapshot
            return snapshot

    def restore_snapshot(self, snapshot_id: str, tenant_id: str) -> MemorySnapshot:
        """Restores memory items from an immutable snapshot."""
        with self._lock:
            snapshot = self._snapshots.get(snapshot_id)
            if not snapshot:
                raise ValueError(f"Memory snapshot '{snapshot_id}' not found.")
            if snapshot.tenant_id != tenant_id:
                raise TenantAccessError("Snapshot tenant mismatch during restore.")

            # Re-hydrate memory store
            for item in snapshot.items:
                store_key = (item.task_id, item.tenant_id, item.key)
                self._memory_store[store_key] = item

            return snapshot

    def _resolve_conflict(self, existing: MemoryItem, incoming: MemoryItem) -> MemoryItem:
        """
        Deterministic authority conflict resolution:
        Lower integer value in MemoryTrustHierarchy represents higher authority.
        Security Authority (1) > Verified Tool (2) > User Constraints (3) > Evidence (4) > LLM (6).
        """
        # Invariant: LLM output can NEVER overwrite deterministic security or verified tools
        if incoming.trust_level > existing.trust_level:
            # Incoming is lower authority: keep existing, but append to provenance
            existing.provenance_chain.append(
                f"Ignored lower-authority overwrite attempt from {incoming.source.value} (Trust Level {incoming.trust_level.value})"
            )
            return existing

        # Incoming is higher or equal authority: accept incoming
        incoming.provenance_chain.extend(existing.provenance_chain)
        incoming.provenance_chain.append(
            f"Superceded previous value from {existing.source.value} (Trust Level {existing.trust_level.value})"
        )
        return incoming
