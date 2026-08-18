"""
SECUROXI AI Intelligence 2.0 — Plan Validator
Performs deterministic pre-execution validation of generated plans:
checks DAG cycles, tool registry existence, tenant boundaries, and security precedence invariants.
"""

from typing import Dict, Any, List, Set, Optional
from securoxi.orchestrator.planning.models import Plan, PlanNodeSpec
from securoxi.orchestrator.planning.types import PlanningStatus, TaskIntent
from securoxi.orchestrator.tools import ToolRegistry
from securoxi.orchestrator.errors import (
    ToolNotFoundError,
    PolicyDeniedError,
    TenantAccessError,
    InvalidStateTransitionError,
    ToolValidationError,
)


class PlanValidator:
    """Deterministic validator enforcing safety and structural invariants on plans."""

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        self.tool_registry = tool_registry

    def validate_plan(self, plan: Plan, tenant_id: str = "TENANT-DEFAULT") -> bool:
        """
        Validates the plan. If invalid, raises a specific Orchestrator error and marks plan as REJECTED.
        Returns True on successful validation.
        """
        try:
            # 1. Validate Node Count
            if not plan.nodes:
                raise ToolValidationError("Plan contains no execution nodes.")

            node_map: Dict[str, PlanNodeSpec] = {n.node_id: n for n in plan.nodes}

            # 2. Validate Dependencies Exist
            for node in plan.nodes:
                for dep_id in node.dependencies:
                    if dep_id not in node_map:
                        raise ToolValidationError(
                            f"Node '{node.name}' ({node.node_id}) has unresolved dependency '{dep_id}'"
                        )

            # 3. Check for Acyclic Graph (No Cycles)
            self._validate_acyclic(plan.nodes)

            # 4. Validate Tool Registration
            if self.tool_registry:
                for node in plan.nodes:
                    if node.tool_id:
                        # Will raise ToolNotFoundError if tool is not registered
                        tool_def = self.tool_registry.get(node.tool_id)
                        if tool_def.tenant_scope and tool_def.tenant_scope != tenant_id:
                            raise TenantAccessError(
                                f"Plan requires tool '{node.tool_id}' scoped to '{tool_def.tenant_scope}', which is unauthorized for tenant '{tenant_id}'"
                            )

            # 5. Enforce Critical Security Invariant: Security Scan MUST Precede Screening
            if plan.intent in {TaskIntent.CANDIDATE_SCREENING, TaskIntent.MIXED_WORKFLOW}:
                self._validate_security_precedence(plan.nodes)

            plan.status = PlanningStatus.VALIDATED
            return True

        except Exception as val_err:
            plan.status = PlanningStatus.REJECTED
            raise val_err

    def _validate_acyclic(self, nodes: List[PlanNodeSpec]):
        """Ensures plan nodes form a strict DAG with no cycles."""
        adj: Dict[str, List[str]] = {n.node_id: list(n.dependencies) for n in nodes}
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            for neighbor in adj.get(node_id, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node_id)
            return False

        for node_id in adj:
            if node_id not in visited:
                if dfs(node_id):
                    raise InvalidStateTransitionError(f"Plan contains a cyclic dependency cycle involving node {node_id}")

    def _validate_security_precedence(self, nodes: List[PlanNodeSpec]):
        """
        Guarantees that no screening, JD matching, or candidate ranking node can execute
        without an upstream Security Scan and Security Filter node.
        """
        node_names = {n.name.lower(): n for n in nodes}
        has_security_scan = any("security" in n.name.lower() or "scan" in n.name.lower() for n in nodes)
        has_screening = any("screen" in n.name.lower() or "rank" in n.name.lower() for n in nodes)

        if has_screening and not has_security_scan:
            raise PolicyDeniedError(
                "Security Policy Violation: Screening or ranking nodes cannot be planned without an upstream security scan."
            )
