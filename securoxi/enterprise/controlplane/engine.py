"""
SECUROXI AI Intelligence 2.0 — Enterprise Intelligence Control Plane Engine (Phase 9 Stage 54)
Central coordination and governance layer across Security, Policy, Identity, Governance, and Evaluation authorities.
"""

from typing import Dict, Any, List, Optional
import time
from securoxi.enterprise.controlplane.types import (
    PolicyDomain,
    PolicyStatus,
    CapabilityStatus,
    EvaluationGateState,
    ControlPlaneDecision,
)
from securoxi.enterprise.controlplane.models import (
    PolicyDefinition,
    CapabilityDefinition,
    EnterpriseDecisionContext,
    ControlPlaneSnapshot,
)
from securoxi.logger import get_logger

logger = get_logger("enterprise.controlplane.engine")


class EnterpriseControlPlane:
    """
    Unified Enterprise Intelligence Control Plane & Policy Fabric.
    Coordinates specialized authorities, evaluates effective decision contexts,
    and enforces platform-wide safety limits without overriding domain engines.
    """

    def __init__(self):
        self._policies: Dict[str, PolicyDefinition] = {}            # policy_id -> PolicyDefinition
        self._capabilities: Dict[str, CapabilityDefinition] = {}    # capability_id -> CapabilityDefinition
        self._snapshots: Dict[str, ControlPlaneSnapshot] = {}
        self._safe_mode: bool = False

    def set_safe_mode(self, enabled: bool):
        """Toggles global operational safe mode / kill switch."""
        self._safe_mode = enabled
        logger.warning(f"Control Plane Safe Mode set to: {enabled}")

    def register_policy(
        self,
        organization_id: str,
        domain: PolicyDomain,
        rules: Dict[str, Any],
        workspace_id: Optional[str] = None,
        created_by: str = "SYSTEM_ADMIN",
        approved_by: Optional[str] = "GOVERNANCE_BOARD",
    ) -> PolicyDefinition:
        """Registers an active, versioned policy definition."""
        policy = PolicyDefinition(
            organization_id=organization_id,
            workspace_id=workspace_id,
            domain=domain,
            rules=rules,
            created_by=created_by,
            approved_by=approved_by,
            status=PolicyStatus.ACTIVE,
        )
        self._policies[policy.policy_id] = policy
        logger.info(f"Registered Policy '{policy.policy_id}' ({domain.value}) for Org '{organization_id}'")
        return policy

    def rollback_policy(self, policy_id: str) -> Optional[PolicyDefinition]:
        """Rolls back an existing policy by creating a new version marked ROLLED_BACK."""
        if policy_id not in self._policies:
            return None

        old_pol = self._policies[policy_id]
        old_pol.status = PolicyStatus.ROLLED_BACK

        new_pol = PolicyDefinition(
            organization_id=old_pol.organization_id,
            workspace_id=old_pol.workspace_id,
            domain=old_pol.domain,
            version=old_pol.version + 1,
            rules={"rollback_from": policy_id},
            status=PolicyStatus.ACTIVE,
            created_by="SYSTEM_ROLLBACK",
        )
        self._policies[new_pol.policy_id] = new_pol
        logger.info(f"Rolled back Policy '{policy_id}' -> New Active Policy '{new_pol.policy_id}'")
        return new_pol

    def register_capability(
        self,
        organization_id: str,
        name: str,
        category: str,
        required_permissions: List[str],
        allowed_autonomy_level: str = "L2_HUMAN_APPROVAL_REQUIRED",
        evaluation_state: EvaluationGateState = EvaluationGateState.PASS,
    ) -> CapabilityDefinition:
        """
        Registers a tool/agent capability.
        If evaluation_state is FAIL, status is deterministically set to DISABLED.
        """
        status = CapabilityStatus.ENABLED if evaluation_state != EvaluationGateState.FAIL else CapabilityStatus.DISABLED

        cap = CapabilityDefinition(
            organization_id=organization_id,
            name=name,
            category=category,
            required_permissions=required_permissions,
            allowed_autonomy_level=allowed_autonomy_level,
            status=status,
            evaluation_state=evaluation_state,
        )
        self._capabilities[cap.capability_id] = cap
        logger.info(f"Registered Capability '{cap.capability_id}' ('{name}') Status={status.value}")
        return cap

    def evaluate_decision(
        self,
        organization_id: str,
        workspace_id: str,
        actor_id: str,
        requested_action: str,
        target_security_state: str = "SAFE",
        evaluation_state: EvaluationGateState = EvaluationGateState.PASS,
        is_high_impact: bool = False,
    ) -> ControlPlaneSnapshot:
        """
        Evaluates unified decision context across specialized authorities:
        1. Security Authority Gate: HIGH_RISK / UNINSPECTABLE -> DENY
        2. Safe Mode Gate: Active safe mode -> REQUIRE_APPROVAL
        3. Evaluation Gate: FAIL -> DENY
        4. Autonomy / Governance Gate: High-impact action -> REQUIRE_APPROVAL
        5. Otherwise: ALLOW
        """
        context = EnterpriseDecisionContext(
            organization_id=organization_id,
            workspace_id=workspace_id,
            actor_id=actor_id,
            security_state=target_security_state,
            evaluation_state=evaluation_state,
        )

        # 1. Deterministic Security Authority
        if target_security_state in {"HIGH_RISK", "UNINSPECTABLE"}:
            decision = ControlPlaneDecision.DENY
            reason = f"Security Gate Barrier: Target resource is {target_security_state}"
        # 2. Operational Safe Mode
        elif self._safe_mode:
            decision = ControlPlaneDecision.REQUIRE_APPROVAL
            reason = "Operational Safe Mode active - human approval required for all actions"
        # 3. Stage 33 Evaluation Gate
        elif evaluation_state == EvaluationGateState.FAIL:
            decision = ControlPlaneDecision.DENY
            reason = "Stage 33 Quality Gate Barrier: Capability failed automated regression evaluation"
        # 4. High-Impact Action Governance Gate
        elif is_high_impact:
            decision = ControlPlaneDecision.REQUIRE_APPROVAL
            reason = "High-impact mutation requires Stage 23 Human Approval"
        # 5. Passed All Gates
        else:
            decision = ControlPlaneDecision.ALLOW
            reason = "All deterministic security, policy, and evaluation checks passed"

        snapshot = ControlPlaneSnapshot(
            organization_id=organization_id,
            workspace_id=workspace_id,
            decision=decision,
            reason=reason,
            context=context,
        )
        self._snapshots[snapshot.snapshot_id] = snapshot
        logger.info(f"Control Plane Decision: {decision.value} for Org '{organization_id}' ({reason})")
        return snapshot

    def get_policies(self, organization_id: str) -> List[PolicyDefinition]:
        """Returns policies strictly scoped by tenant."""
        return [p for p in self._policies.values() if p.organization_id == organization_id and p.status == PolicyStatus.ACTIVE]
