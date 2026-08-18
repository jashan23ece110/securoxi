"""
SECUROXI AI Intelligence 2.0 — Orchestrator Budget & Resource Limiter
Enforces hard execution bounds on steps, tool invocations, wall-clock latency, tokens, and cost.
"""

import time
import threading
from typing import Dict, Any, Optional
from securoxi.orchestrator.models import TaskBudget
from securoxi.orchestrator.errors import BudgetExhaustedError, DeadlineExceededError


class BudgetTracker:
    """Thread-safe budget tracker that monitors and enforces task limits."""

    def __init__(self, budget: Optional[TaskBudget] = None, deadline: Optional[float] = None):
        self.budget = budget or TaskBudget()
        self.deadline = deadline
        self.start_time = time.time()
        self.lock = threading.Lock()

        # Mutable counters
        self.current_steps = 0
        self.current_tool_calls = 0
        self.current_parallel_branches = 0
        self.current_tokens = 0
        self.current_cost_usd = 0.0

    def check_time_limit(self):
        """Verifies wall-clock runtime against max_runtime_sec and explicit deadline."""
        now = time.time()
        elapsed = now - self.start_time

        if elapsed > self.budget.max_runtime_sec:
            raise DeadlineExceededError(
                f"Maximum runtime exceeded: elapsed {elapsed:.2f}s > limit {self.budget.max_runtime_sec:.2f}s",
                details={"elapsed_sec": elapsed, "max_runtime_sec": self.budget.max_runtime_sec}
            )

        if self.deadline and now > self.deadline:
            raise DeadlineExceededError(
                f"Task deadline exceeded: current {now:.2f} > deadline {self.deadline:.2f}",
                details={"current_time": now, "deadline": self.deadline}
            )

    def record_step(self):
        """Increments step count and enforces max_steps budget."""
        with self.lock:
            self.check_time_limit()
            if self.current_steps >= self.budget.max_steps:
                raise BudgetExhaustedError(
                    f"Maximum step budget exhausted: {self.current_steps} >= {self.budget.max_steps}",
                    details={"current_steps": self.current_steps, "max_steps": self.budget.max_steps}
                )
            self.current_steps += 1

    def record_tool_call(self):
        """Increments tool invocation count and enforces max_tool_calls budget."""
        with self.lock:
            self.check_time_limit()
            if self.current_tool_calls >= self.budget.max_tool_calls:
                raise BudgetExhaustedError(
                    f"Maximum tool call budget exhausted: {self.current_tool_calls} >= {self.budget.max_tool_calls}",
                    details={"current_tool_calls": self.current_tool_calls, "max_tool_calls": self.budget.max_tool_calls}
                )
            self.current_tool_calls += 1

    def record_tokens_and_cost(self, tokens: int = 0, cost_usd: float = 0.0):
        """Updates token and cost telemetry, enforcing respective ceilings."""
        with self.lock:
            self.check_time_limit()
            self.current_tokens += tokens
            self.current_cost_usd += cost_usd

            if self.budget.max_tokens and self.current_tokens > self.budget.max_tokens:
                raise BudgetExhaustedError(
                    f"Token ceiling exceeded: {self.current_tokens} > {self.budget.max_tokens}",
                    details={"tokens": self.current_tokens, "max_tokens": self.budget.max_tokens}
                )

            if self.budget.max_cost_usd and self.current_cost_usd > self.budget.max_cost_usd:
                raise BudgetExhaustedError(
                    f"Cost budget exceeded: ${self.current_cost_usd:.4f} > ${self.budget.max_cost_usd:.4f}",
                    details={"cost_usd": self.current_cost_usd, "max_cost_usd": self.budget.max_cost_usd}
                )

    def get_remaining_runtime(self) -> float:
        """Returns remaining seconds before budget or deadline expires."""
        elapsed = time.time() - self.start_time
        remaining_runtime = max(0.0, self.budget.max_runtime_sec - elapsed)
        if self.deadline:
            remaining_deadline = max(0.0, self.deadline - time.time())
            return min(remaining_runtime, remaining_deadline)
        return remaining_runtime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_steps": self.current_steps,
            "max_steps": self.budget.max_steps,
            "current_tool_calls": self.current_tool_calls,
            "max_tool_calls": self.budget.max_tool_calls,
            "elapsed_runtime_sec": time.time() - self.start_time,
            "max_runtime_sec": self.budget.max_runtime_sec,
            "current_tokens": self.current_tokens,
            "max_tokens": self.budget.max_tokens,
            "current_cost_usd": self.current_cost_usd,
            "max_cost_usd": self.budget.max_cost_usd,
            "remaining_runtime_sec": self.get_remaining_runtime(),
        }
