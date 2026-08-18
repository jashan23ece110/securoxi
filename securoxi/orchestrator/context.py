"""
SECUROXI AI Intelligence 2.0 — Structured Runtime Execution Context
Thread-safe context passing tenant identity, security credentials, shared state,
DAG reference, and cancellation token through every node and tool execution.
"""

import time
import threading
from typing import Dict, Any, List, Optional
from securoxi.orchestrator.models import Task, Run
from securoxi.orchestrator.types import TrustLevel
from securoxi.orchestrator.budget import BudgetTracker


class ExecutionContext:
    """Structured, immutable-by-default execution context for a run."""

    def __init__(
        self,
        task: Task,
        run: Run,
        budget_tracker: Optional[BudgetTracker] = None,
        actor_permissions: Optional[List[str]] = None,
        actor_trust_level: TrustLevel = TrustLevel.LOW_RISK,
    ):
        self.task = task
        self.run = run
        self.tenant_id = task.tenant_id
        self.actor_id = task.actor_id
        self.actor_permissions = actor_permissions or ["*"]
        self.actor_trust_level = actor_trust_level
        self.budget_tracker = budget_tracker or BudgetTracker(task.budget, task.deadline)

        self._shared_state: Dict[str, Any] = {}
        self._cancellation_event = threading.Event()
        self._lock = threading.Lock()
        self._provenance_log: List[Dict[str, Any]] = []

    @property
    def is_cancelled(self) -> bool:
        return self._cancellation_event.is_set()

    def cancel(self):
        """Signals graceful cancellation across all active and pending nodes."""
        self._cancellation_event.set()

    def set_shared_value(self, key: str, value: Any, source_node_id: Optional[str] = None):
        """Thread-safely stores shared intermediate data with provenance tracking."""
        with self._lock:
            self._shared_state[key] = value
            self._provenance_log.append({
                "key": key,
                "source_node_id": source_node_id,
                "timestamp": time.time()
            })

    def get_shared_value(self, key: str, default: Any = None) -> Any:
        """Retrieves a shared value."""
        with self._lock:
            return self._shared_state.get(key, default)

    def get_all_shared_state(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._shared_state)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task.task_id,
            "run_id": self.run.run_id,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "actor_permissions": self.actor_permissions,
            "actor_trust_level": self.actor_trust_level.value,
            "is_cancelled": self.is_cancelled,
            "budget": self.budget_tracker.to_dict(),
            "shared_state_keys": list(self._shared_state.keys()),
        }
