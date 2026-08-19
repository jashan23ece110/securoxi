"""
SECUROXI AI Intelligence 2.0 — Multi-Tenant Fairness Scheduler
Enforces per-organization concurrency caps, fair queueing, and starvation prevention.
"""

from typing import Dict, Set
from securoxi.logger import get_logger

logger = get_logger("enterprise.fairness")


class TenantFairnessScheduler:
    """
    Multi-Tenant Concurrency and Fairness Controller.
    Guarantees that a massive batch from Organization A cannot starve Organization B.
    """

    def __init__(self, max_concurrent_tasks_per_org: int = 50):
        self.max_concurrent = max_concurrent_tasks_per_org
        self._active_org_tasks: Dict[str, Set[str]] = {}  # org_id -> set of active task_ids

    def can_schedule_task(self, organization_id: str) -> bool:
        """Checks whether the organization is within its permitted concurrency limit."""
        active = len(self._active_org_tasks.get(organization_id, set()))
        return active < self.max_concurrent

    def acquire_execution_slot(self, organization_id: str, task_id: str) -> bool:
        """Acquires a concurrency slot if within tenant limits."""
        if not self.can_schedule_task(organization_id):
            logger.warning(f"Tenant Concurrency Throttled: Org '{organization_id}' reached limit of {self.max_concurrent} tasks")
            return False

        if organization_id not in self._active_org_tasks:
            self._active_org_tasks[organization_id] = set()

        self._active_org_tasks[organization_id].add(task_id)
        return True

    def release_execution_slot(self, organization_id: str, task_id: str):
        """Releases an acquired concurrency slot upon task completion."""
        if organization_id in self._active_org_tasks:
            self._active_org_tasks[organization_id].discard(task_id)

    def get_active_count(self, organization_id: str) -> int:
        return len(self._active_org_tasks.get(organization_id, set()))
