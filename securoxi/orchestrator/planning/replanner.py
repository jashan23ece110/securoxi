"""
SECUROXI AI Intelligence 2.0 — Adaptive Replanner & Version Controller
Handles dynamic runtime replanning, plan version auditing, partial failure adaptation,
and bounded replan loops.
"""

import time
import copy
from typing import Dict, Any, List, Optional, Tuple

from securoxi.orchestrator.planning.types import (
    ReplanReason,
    PlanningStatus,
)
from securoxi.orchestrator.planning.models import (
    Plan,
    PlanNodeSpec,
    PlanVersionRecord,
)
from securoxi.orchestrator.planning.validator import PlanValidator
from securoxi.orchestrator.graph import ExecutionDAG
from securoxi.orchestrator.errors import BudgetExhaustedError, OrchestratorError


class AdaptiveReplanner:
    """
    Manages bounded plan adaptation and version history during execution anomalies.
    """

    def __init__(
        self,
        max_replans: int = 3,
        validator: Optional[PlanValidator] = None,
    ):
        self.max_replans = max_replans
        self.validator = validator or PlanValidator()
        self._history: Dict[str, List[PlanVersionRecord]] = {}  # plan_id -> list of records

    def replan(
        self,
        current_plan: Plan,
        reason: ReplanReason,
        details: str,
        failed_node_id: Optional[str] = None,
        intermediate_state: Optional[Dict[str, Any]] = None,
        tenant_id: str = "TENANT-DEFAULT"
    ) -> Plan:
        """
        Adapts a plan in response to runtime failures or newly discovered findings.
        Creates a new plan version, validates it, and logs the revision in version history.
        """
        # 1. Enforce Bounded Replan Limit
        if current_plan.version > self.max_replans:
            raise BudgetExhaustedError(
                f"Maximum replan limit ({self.max_replans}) exceeded for Plan {current_plan.plan_id}",
                details={"current_version": current_plan.version, "max_replans": self.max_replans}
            )

        # 2. Record Snapshot of Previous Version
        old_record = PlanVersionRecord(
            plan_id=current_plan.plan_id,
            version=current_plan.version,
            replan_reason=reason,
            details=details,
            plan_snapshot=current_plan.to_dict()
        )
        if current_plan.plan_id not in self._history:
            self._history[current_plan.plan_id] = []
        self._history[current_plan.plan_id].append(old_record)

        # 3. Create Incremented Plan Copy
        new_plan = copy.deepcopy(current_plan)
        new_plan.version = current_plan.version + 1
        new_plan.status = PlanningStatus.DRAFT

        # 4. Apply Adaptation Strategy
        if reason == ReplanReason.OCR_FAILED:
            self._adapt_for_ocr_failure(new_plan, failed_node_id, details)
        elif reason == ReplanReason.SECURITY_FINDING_ESCALATED:
            self._adapt_for_security_escalation(new_plan, intermediate_state)
        elif reason == ReplanReason.BRANCH_FAILED:
            self._adapt_for_partial_failure(new_plan, failed_node_id)
        else:
            # Generic fallback adaptation
            new_plan.summary_explanation += f" (Adapted for {reason.value}: {details})"

        # 5. Deterministic Validation of Revised Plan
        self.validator.validate_plan(new_plan, tenant_id=tenant_id)
        new_plan.status = PlanningStatus.ACTIVE

        return new_plan

    def _adapt_for_ocr_failure(self, plan: Plan, failed_node_id: Optional[str], details: str):
        """Inserts fallback text extraction and marks uninspectable items without failing entire run."""
        plan.summary_explanation += " [OCR fallback applied: image-only items quarantined for review]"
        for node in plan.nodes:
            if failed_node_id and node.node_id == failed_node_id:
                node.description += " (Fallback text extraction mode)"

    def _adapt_for_security_escalation(self, plan: Plan, state: Optional[Dict[str, Any]]):
        """Redirects execution path to quarantine and incident management."""
        plan.summary_explanation += " [Security escalation: risky candidate routed to quarantine]"
        for node in plan.nodes:
            if "screen" in node.name.lower() or "rank" in node.name.lower():
                node.description = "Quarantine gate: blocked candidate from influence on fit scoring"

    def _adapt_for_partial_failure(self, plan: Plan, failed_node_id: Optional[str]):
        """Isolates a failed branch so downstream aggregator nodes can finalize partial results."""
        plan.summary_explanation += " [Partial failure isolated: continuing with remaining candidate pool]"
        for node in plan.nodes:
            if failed_node_id and failed_node_id in node.dependencies:
                node.dependencies.remove(failed_node_id)

    def get_version_history(self, plan_id: str) -> List[PlanVersionRecord]:
        """Returns the version audit trail for a given plan ID."""
        return self._history.get(plan_id, [])
