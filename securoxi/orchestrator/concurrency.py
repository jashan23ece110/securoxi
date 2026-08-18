"""
SECUROXI AI Intelligence 2.0 — Orchestrator Concurrency & Backpressure Controller
Controls execution parallelism across global, tenant, tool, and run scopes.
"""

import threading
from typing import Dict, Any, Optional
from securoxi.orchestrator.errors import ConcurrencyLimitExceededError


class ConcurrencyController:
    """Multi-tiered concurrency limiter to prevent resource exhaustion and starvation."""

    def __init__(
        self,
        max_global_concurrency: int = 50,
        max_tenant_concurrency: int = 20,
        max_tool_concurrency: int = 10,
        max_run_concurrency: int = 8,
    ):
        self.max_global_concurrency = max_global_concurrency
        self.max_tenant_concurrency = max_tenant_concurrency
        self.max_tool_concurrency = max_tool_concurrency
        self.max_run_concurrency = max_run_concurrency

        self._lock = threading.Lock()
        self._global_active = 0
        self._tenant_active: Dict[str, int] = {}
        self._tool_active: Dict[str, int] = {}
        self._run_active: Dict[str, int] = {}

    def acquire(self, tenant_id: str, run_id: str, tool_id: Optional[str] = None):
        """Acquires execution slots across all relevant scopes. Raises if limits exceeded."""
        with self._lock:
            if self._global_active >= self.max_global_concurrency:
                raise ConcurrencyLimitExceededError(
                    f"Global concurrency limit reached ({self._global_active}/{self.max_global_concurrency})"
                )

            tenant_count = self._tenant_active.get(tenant_id, 0)
            if tenant_count >= self.max_tenant_concurrency:
                raise ConcurrencyLimitExceededError(
                    f"Tenant concurrency limit reached for {tenant_id} ({tenant_count}/{self.max_tenant_concurrency})"
                )

            run_count = self._run_active.get(run_id, 0)
            if run_count >= self.max_run_concurrency:
                raise ConcurrencyLimitExceededError(
                    f"Run concurrency limit reached for {run_id} ({run_count}/{self.max_run_concurrency})"
                )

            if tool_id:
                tool_count = self._tool_active.get(tool_id, 0)
                if tool_count >= self.max_tool_concurrency:
                    raise ConcurrencyLimitExceededError(
                        f"Tool concurrency limit reached for {tool_id} ({tool_count}/{self.max_tool_concurrency})"
                    )

            # Increment slots
            self._global_active += 1
            self._tenant_active[tenant_id] = tenant_count + 1
            self._run_active[run_id] = run_count + 1
            if tool_id:
                self._tool_active[tool_id] = self._tool_active.get(tool_id, 0) + 1

    def release(self, tenant_id: str, run_id: str, tool_id: Optional[str] = None):
        """Releases execution slots across scopes."""
        with self._lock:
            self._global_active = max(0, self._global_active - 1)
            if tenant_id in self._tenant_active:
                self._tenant_active[tenant_id] = max(0, self._tenant_active[tenant_id] - 1)
            if run_id in self._run_active:
                self._run_active[run_id] = max(0, self._run_active[run_id] - 1)
            if tool_id and tool_id in self._tool_active:
                self._tool_active[tool_id] = max(0, self._tool_active[tool_id] - 1)

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "global_active": self._global_active,
                "global_max": self.max_global_concurrency,
                "tenant_active": dict(self._tenant_active),
                "tool_active": dict(self._tool_active),
                "run_active": dict(self._run_active),
            }
