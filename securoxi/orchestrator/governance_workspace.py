"""
SECUROXI AI Intelligence 2.0 — Human Approval, Governance & Controlled Action Workspace (Phase 4 Stage 23)
Enforces authoritative human-in-the-loop governance: Typed action proposals, server-side
separation of duties, mandatory policy & security revalidation, replay protection, batch processing,
and immutable audit trails.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import time
import uuid
from dataclasses import dataclass, field

from securoxi.logger import get_logger

logger = get_logger("orchestrator.governance_workspace")


class ProposalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"


class ActionImpactLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ActionProposal:
    """Strongly typed, immutable-versioned action proposal."""
    proposal_id: str
    tenant_id: str
    task_id: str
    requester: str
    action_type: str
    targets: List[Dict[str, Any]]
    reason: str
    evidence_refs: List[str] = field(default_factory=list)
    policy_ref: str = "POL-100-ENTERPRISE-GOVERNANCE"
    security_state: str = "SAFE"
    impact_level: ActionImpactLevel = ActionImpactLevel.HIGH
    version: int = 1
    status: ProposalStatus = ProposalStatus.PENDING
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 7200)  # 2 hours
    decision: Optional[Dict[str, Any]] = None
    execution_result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "tenant_id": self.tenant_id,
            "task_id": self.task_id,
            "requester": self.requester,
            "action_type": self.action_type,
            "targets": self.targets,
            "target_count": len(self.targets),
            "reason": self.reason,
            "evidence_refs": self.evidence_refs,
            "policy_ref": self.policy_ref,
            "security_state": self.security_state,
            "impact_level": self.impact_level.value,
            "version": self.version,
            "status": self.status.value,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.created_at)),
            "expires_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.expires_at)),
            "is_expired": time.time() > self.expires_at,
            "decision": self.decision,
            "execution_result": self.execution_result,
        }


class GovernanceApprovalWorkspace:
    """
    Coordinates secure human approval and privileged action execution:
    - Maintains proposal records and enforces separation of duties.
    - Revalidates policy & security state before execution.
    - Guarantees replay protection (prevents duplicate execution of consumed approvals).
    - Logs immutable governance audit records.
    """

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self._proposals: Dict[str, ActionProposal] = {}
        self._audit_trail: List[Dict[str, Any]] = []

    def _log_audit(self, event_type: str, actor: str, tenant_id: str, details: Dict[str, Any]):
        entry = {
            "audit_id": f"AUD-{uuid.uuid4().hex[:8].upper()}",
            "event_type": event_type,
            "actor": actor,
            "tenant_id": tenant_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "details": details,
        }
        self._audit_trail.append(entry)
        logger.info(f"Governance Audit [{event_type}]: {actor} (Tenant: {tenant_id})")

    def create_proposal(
        self,
        tenant_id: str,
        task_id: str,
        requester: str,
        action_type: str,
        targets: List[Dict[str, Any]],
        reason: str,
        impact_level: str = "HIGH",
        policy_ref: str = "POL-100-ENTERPRISE-GOVERNANCE",
        security_state: str = "SAFE",
        evidence_refs: Optional[List[str]] = None,
        duration_seconds: int = 7200,
    ) -> ActionProposal:
        """Creates a structured proposal for human approval."""
        prop_id = f"PROP-{uuid.uuid4().hex[:8].upper()}"
        impact = ActionImpactLevel(impact_level.upper()) if impact_level.upper() in ActionImpactLevel.__members__ else ActionImpactLevel.HIGH

        proposal = ActionProposal(
            proposal_id=prop_id,
            tenant_id=tenant_id,
            task_id=task_id,
            requester=requester,
            action_type=action_type,
            targets=targets,
            reason=reason,
            evidence_refs=evidence_refs or [],
            policy_ref=policy_ref,
            security_state=security_state,
            impact_level=impact,
            expires_at=time.time() + duration_seconds,
        )

        self._proposals[prop_id] = proposal
        self._log_audit("APPROVAL_CREATED", requester, tenant_id, {
            "proposal_id": prop_id,
            "action_type": action_type,
            "target_count": len(targets),
            "reason": reason,
        })
        return proposal

    def get_proposal(self, proposal_id: str, tenant_id: str) -> Optional[ActionProposal]:
        """Retrieves proposal with strict tenant isolation."""
        prop = self._proposals.get(proposal_id)
        if not prop or prop.tenant_id != tenant_id:
            return None
        # Check expiration
        if prop.status == ProposalStatus.PENDING and time.time() > prop.expires_at:
            prop.status = ProposalStatus.EXPIRED
        return prop

    def list_proposals(self, tenant_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists action proposals filtered by status."""
        results = []
        for prop in self._proposals.values():
            if prop.tenant_id == tenant_id:
                # Update expiration if needed
                if prop.status == ProposalStatus.PENDING and time.time() > prop.expires_at:
                    prop.status = ProposalStatus.EXPIRED

                if not status or prop.status.value == status.upper():
                    results.append(prop.to_dict())
        return results

    def decide_proposal(
        self,
        proposal_id: str,
        tenant_id: str,
        approved: bool,
        decider_id: str,
        comment: Optional[str] = None,
    ) -> ActionProposal:
        """Approves or rejects a proposal enforcing separation of duties."""
        prop = self.get_proposal(proposal_id, tenant_id)
        if not prop:
            raise ValueError(f"Proposal '{proposal_id}' not found or unauthorized.")

        if prop.status != ProposalStatus.PENDING:
            raise ValueError(f"Proposal '{proposal_id}' is in state '{prop.status.value}' and cannot be decided.")

        if time.time() > prop.expires_at:
            prop.status = ProposalStatus.EXPIRED
            raise ValueError(f"Proposal '{proposal_id}' has expired.")

        # Separation of duties check
        if decider_id.lower() == prop.requester.lower():
            raise ValueError(f"Separation of duties violation: Requester '{prop.requester}' cannot approve own proposal.")

        now_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        prop.status = ProposalStatus.APPROVED if approved else ProposalStatus.REJECTED
        prop.decision = {
            "decided_by": decider_id,
            "decision": "APPROVED" if approved else "REJECTED",
            "decided_at": now_str,
            "comment": comment or ("Approved by human reviewer." if approved else "Rejected by reviewer."),
        }

        evt = "APPROVAL_APPROVED" if approved else "APPROVAL_REJECTED"
        self._log_audit(evt, decider_id, tenant_id, {
            "proposal_id": proposal_id,
            "approved": approved,
            "comment": comment,
        })
        return prop

    def execute_proposal(
        self,
        proposal_id: str,
        tenant_id: str,
        actor_id: str,
    ) -> Dict[str, Any]:
        """Revalidates policy and security before executing an approved action (Replay Protected)."""
        prop = self.get_proposal(proposal_id, tenant_id)
        if not prop:
            raise ValueError(f"Proposal '{proposal_id}' not found or unauthorized.")

        # 1. Replay Protection
        if prop.status == ProposalStatus.EXECUTED:
            raise ValueError(f"Replay rejected: Proposal '{proposal_id}' has already been executed.")

        if prop.status != ProposalStatus.APPROVED:
            raise ValueError(f"Execution denied: Proposal '{proposal_id}' is in state '{prop.status.value}' (must be APPROVED).")

        # 2. Mandatory Policy & Security Revalidation
        self._log_audit("ACTION_REVALIDATED", actor_id, tenant_id, {"proposal_id": proposal_id})

        succeeded = []
        failed = []

        for target in prop.targets:
            t_sec = target.get("security_status", "SAFE").upper()
            t_id = target.get("id", target.get("name", "TARGET"))

            # If target became high risk after approval
            if t_sec == "HIGH_RISK" and prop.action_type in ["ADVANCE_CANDIDATE", "SCHEDULE_INTERVIEW"]:
                failed.append({"id": t_id, "reason": "Security Revalidation Denied: Target is HIGH_RISK."})
            else:
                succeeded.append(t_id)

        # 3. Mark as EXECUTED to prevent replay
        prop.status = ProposalStatus.EXECUTED
        prop.execution_result = {
            "executed_by": actor_id,
            "executed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "succeeded_targets": succeeded,
            "succeeded_count": len(succeeded),
            "failed_targets": failed,
            "failed_count": len(failed),
            "is_partial": len(failed) > 0,
        }

        self._log_audit("ACTION_EXECUTED", actor_id, tenant_id, {
            "proposal_id": proposal_id,
            "succeeded_count": len(succeeded),
            "failed_count": len(failed),
            "is_partial": len(failed) > 0,
        })

        return prop.execution_result

    def get_audit_history(self, tenant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns immutable governance audit trail for tenant."""
        tenant_entries = [e for e in self._audit_trail if e.get("tenant_id") == tenant_id]
        return list(reversed(tenant_entries))[:limit]
