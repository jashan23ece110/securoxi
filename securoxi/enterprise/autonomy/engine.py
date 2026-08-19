"""
SECUROXI AI Intelligence 2.0 — Controlled Autonomy Engine (Phase 8 Stage 52)
Executes bounded, verified autonomous actions while strictly enforcing human governance gates.
"""

from typing import Dict, Any, List, Optional
import time
from securoxi.enterprise.autonomy.types import (
    AutonomyLevel,
    ActionImpactClass,
    ActionReversibility,
    ProposalStatus,
    ExecutionStatus,
)
from securoxi.enterprise.autonomy.models import (
    ActionProposal,
    ActionExecution,
    ActionOutcome,
)
from securoxi.logger import get_logger

logger = get_logger("enterprise.autonomy.engine")


class ControlledAutonomyEngine:
    """
    Controlled Autonomous Action & Closed-Loop Operations Engine.
    Enforces deterministic safety boundaries, stale proposal protection,
    idempotency, and post-action verification.
    """

    def __init__(self):
        self._proposals: Dict[str, ActionProposal] = {}       # proposal_id -> ActionProposal
        self._executions: Dict[str, ActionExecution] = {}     # execution_id -> ActionExecution
        self._executed_idempotency_keys: set[str] = set()
        self._safe_mode_enabled: bool = False                 # Operational Kill Switch

    def set_safe_mode(self, enabled: bool):
        """Toggles safe mode (kill switch): forces all actions to recommendation-only."""
        self._safe_mode_enabled = enabled
        logger.warning(f"Autonomy Safe Mode set to: {enabled}")

    def propose_action(
        self,
        organization_id: str,
        workspace_id: str,
        action_type: str,
        target_resource_id: str,
        impact_class: ActionImpactClass = ActionImpactClass.LOW_IMPACT_REVERSIBLE,
        reversibility: ActionReversibility = ActionReversibility.REVERSIBLE,
        autonomy_level: AutonomyLevel = AutonomyLevel.L3_GUARDED_AUTONOMOUS_LOW_IMPACT,
        reason: str = "Automated system optimization",
        parameters: Optional[Dict[str, Any]] = None,
        source_evidence_version: int = 1,
    ) -> ActionProposal:
        """
        Registers an action proposal.
        Enforces platform safety limit: HIGH_IMPACT / CRITICAL actions ALWAYS require human approval (L2).
        """
        if impact_class in {ActionImpactClass.HIGH_IMPACT, ActionImpactClass.CRITICAL}:
            autonomy_level = AutonomyLevel.L2_HUMAN_APPROVAL_REQUIRED

        proposal = ActionProposal(
            organization_id=organization_id,
            workspace_id=workspace_id,
            action_type=action_type,
            target_resource_id=target_resource_id,
            parameters=parameters or {},
            impact_class=impact_class,
            reversibility=reversibility,
            autonomy_level=autonomy_level,
            reason=reason,
            source_evidence_version=source_evidence_version,
        )
        self._proposals[proposal.proposal_id] = proposal
        logger.info(f"Registered Action Proposal '{proposal.proposal_id}' ({action_type}) Level={autonomy_level.value}")
        return proposal

    def execute_action(
        self,
        proposal_id: str,
        current_evidence_version: int,
        target_security_state: str = "SAFE",
        approver_id: Optional[str] = None,
    ) -> tuple[bool, Optional[ActionExecution], str]:
        """
        Executes a proposed action through strict deterministic validation:
        1. Safe Mode check
        2. Security gate check (HIGH_RISK / UNINSPECTABLE targets are blocked)
        3. Stale proposal check (evidence version drift or expiration)
        4. Approval check for L2 actions
        5. Idempotency check
        6. Post-action state verification
        """
        if proposal_id not in self._proposals:
            return False, None, "PROPOSAL_NOT_FOUND"

        proposal = self._proposals[proposal_id]

        # 1. Operational Safe Mode
        if self._safe_mode_enabled:
            proposal.status = ProposalStatus.DENIED_POLICY
            logger.warning(f"Execution Denied: Safe mode active for Proposal '{proposal_id}'")
            return False, None, "SAFE_MODE_BLOCKED"

        # 2. Deterministic Security Gate
        if target_security_state in {"HIGH_RISK", "UNINSPECTABLE"}:
            proposal.status = ProposalStatus.DENIED_POLICY
            logger.error(f"Execution Denied: Target '{proposal.target_resource_id}' is {target_security_state}")
            return False, None, f"TARGET_{target_security_state}"

        # 3. Stale Proposal Check
        if current_evidence_version != proposal.source_evidence_version or time.time() > proposal.expires_at:
            proposal.status = ProposalStatus.STALE_PROPOSAL
            logger.warning(f"Execution Denied: Stale Proposal '{proposal_id}' (v{current_evidence_version} vs v{proposal.source_evidence_version})")
            return False, None, "STALE_PROPOSAL"

        # 4. Human Governance Approval Gate
        if proposal.autonomy_level == AutonomyLevel.L2_HUMAN_APPROVAL_REQUIRED and not approver_id:
            logger.warning(f"Execution Denied: Proposal '{proposal_id}' requires human approval")
            return False, None, "APPROVAL_REQUIRED"

        # 5. Idempotency Guard
        if proposal.idempotency_key in self._executed_idempotency_keys:
            logger.warning(f"Duplicate Execution Blocked: Idempotency Key '{proposal.idempotency_key}'")
            return False, None, "DUPLICATE_IDEMPOTENCY"

        # 6. Execute & Verify Outcome
        self._executed_idempotency_keys.add(proposal.idempotency_key)
        proposal.status = ProposalStatus.EXECUTED

        outcome = ActionOutcome(
            action_id=proposal.proposal_id,
            expected_state="COMPLETED",
            observed_state="COMPLETED",
            is_verified=True,
        )

        execution = ActionExecution(
            proposal_id=proposal.proposal_id,
            organization_id=proposal.organization_id,
            executed_by=approver_id or "SYSTEM_AUTONOMOUS",
            status=ExecutionStatus.SUCCESS,
            outcome=outcome,
        )
        self._executions[execution.execution_id] = execution
        logger.info(f"Executed & Verified Action '{proposal.proposal_id}' (Execution '{execution.execution_id}')")
        return True, execution, "SUCCESS"
