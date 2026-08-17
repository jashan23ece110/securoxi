"""
SECUROXI AI Phase 3 Stage 8 — Automated Response & Incident Management Framework
Implements the 6-state Incident Lifecycle (DETECTED -> TRIAGED -> INVESTIGATING -> RESPONDED -> RESOLVED -> CLOSED),
incident deduplication, escalation, policy authorization enforcement, and audit trail tracking.
"""

import time
import uuid
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from securoxi.brain.policy_engine import SecuroxiPolicyEngine, PolicyContext, PolicyDecisionAction
from securoxi.logger import get_logger


class IncidentState(str, Enum):
    DETECTED = "DETECTED"
    TRIAGED = "TRIAGED"
    INVESTIGATING = "INVESTIGATING"
    RESPONDED = "RESPONDED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class ResponseActionType(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    QUARANTINE_DOCUMENT = "QUARANTINE_DOCUMENT"
    SUSPEND_PROCESSING = "SUSPEND_PROCESSING"
    NOTIFY_SECURITY_TEAM = "NOTIFY_SECURITY_TEAM"
    CREATE_REVIEW_TASK = "CREATE_REVIEW_TASK"
    MARK_CANDIDATE_MANUAL_REVIEW = "MARK_CANDIDATE_MANUAL_REVIEW"
    REVOKE_INTEGRATION_EVENT = "REVOKE_INTEGRATION_EVENT"


@dataclass
class SecurityIncident:
    """Enterprise Security Incident Object."""
    incident_id: str = field(default_factory=lambda: f"INC-SECUROXI-{uuid.uuid4().hex[:8]}")
    source: str = "CONTINUOUS_MONITOR"
    affected_asset: str = "UNKNOWN_ASSET"
    attack_type: str = "GENERIC_THREAT"
    severity: str = "HIGH"
    risk_score: float = 0.0
    evidence: str = "None"
    attack_graph: Dict[str, Any] = field(default_factory=dict)
    policy_decision: Dict[str, Any] = field(default_factory=dict)
    response_actions: List[str] = field(default_factory=list)
    state: IncidentState = IncidentState.DETECTED
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def log_audit(self, action: str, details: str, actor: str = "SYSTEM"):
        entry = {
            "action": action,
            "details": details,
            "actor": actor,
            "timestamp": time.time()
        }
        self.audit_trail.append(entry)
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "source": self.source,
            "affected_asset": self.affected_asset,
            "attack_type": self.attack_type,
            "severity": self.severity,
            "risk_score": self.risk_score,
            "evidence": self.evidence,
            "attack_graph": self.attack_graph,
            "policy_decision": self.policy_decision,
            "response_actions": self.response_actions,
            "state": self.state.value,
            "assigned_to": self.assigned_to,
            "resolution_notes": self.resolution_notes,
            "audit_trail": self.audit_trail,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class IncidentManager:
    """
    Enterprise Incident Response & Lifecycle Management Engine.
    Enforces policy authorization before executing response actions, deduplicates incidents,
    supports escalation, and logs complete audit trails.
    """

    def __init__(self):
        self.logger = get_logger("securoxi.incident.manager")
        self.policy_engine = SecuroxiPolicyEngine()
        self.incidents: Dict[str, SecurityIncident] = {}
        self.asset_dedup_index: Dict[str, str] = {}  # Maps asset_key -> incident_id

    def create_incident(
        self,
        source: str,
        affected_asset: str,
        attack_type: str,
        risk_score: float,
        evidence: str,
        attack_graph: Optional[Dict[str, Any]] = None,
        llm_recommendation: Optional[str] = None
    ) -> SecurityIncident:
        """
        Deduplicates & creates a new SecurityIncident.
        LLM recommendations are logged, but policy authorization strictly decides response actions!
        """
        asset_key = f"{affected_asset}:{attack_type}"

        # Deduplication check
        if asset_key in self.asset_dedup_index:
            existing_id = self.asset_dedup_index[asset_key]
            existing_inc = self.incidents[existing_id]
            existing_inc.log_audit("DEDUPLICATE_RECORDED", f"Duplicate threat detected for asset '{affected_asset}'.")

            # Escalate if risk score increases!
            if risk_score > existing_inc.risk_score:
                self.logger.warning(f"ESCALATING Incident '{existing_id}': Risk score increased from {existing_inc.risk_score} to {risk_score}.")
                existing_inc.risk_score = risk_score
                existing_inc.severity = "CRITICAL" if risk_score >= 90.0 else "HIGH"
                existing_inc.log_audit("ESCALATED", f"Severity escalated to {existing_inc.severity} due to higher risk score.")

            return existing_inc

        # Policy Engine Authorization (Policy decides, LLM only recommends!)
        ctx = PolicyContext(
            verdict="HIGH_RISK" if risk_score >= 80.0 else "SUSPICIOUS",
            risk_score=risk_score,
            source=source,
            target=affected_asset,
            threat_types=[attack_type]
        )
        policy_dec = self.policy_engine.evaluate_policy(ctx)

        # Map Policy Decision to Automated Response Actions
        response_actions = []
        if policy_dec.action == PolicyDecisionAction.BLOCK:
            response_actions = [ResponseActionType.BLOCK.value, ResponseActionType.NOTIFY_SECURITY_TEAM.value]
        elif policy_dec.action == PolicyDecisionAction.QUARANTINE:
            response_actions = [ResponseActionType.QUARANTINE_DOCUMENT.value, ResponseActionType.CREATE_REVIEW_TASK.value]
        elif policy_dec.action == PolicyDecisionAction.REVIEW:
            response_actions = [ResponseActionType.MARK_CANDIDATE_MANUAL_REVIEW.value, ResponseActionType.CREATE_REVIEW_TASK.value]
        else:
            response_actions = [ResponseActionType.ALLOW.value]

        severity_str = "CRITICAL" if risk_score >= 90.0 else ("HIGH" if risk_score >= 70.0 else "MEDIUM")

        inc = SecurityIncident(
            source=source,
            affected_asset=affected_asset,
            attack_type=attack_type,
            severity=severity_str,
            risk_score=risk_score,
            evidence=evidence,
            attack_graph=attack_graph or {},
            policy_decision=policy_dec.to_dict(),
            response_actions=response_actions,
            state=IncidentState.DETECTED
        )

        inc.log_audit("CREATED", f"Incident created with severity {severity_str}. Authorized actions: {response_actions}")
        if llm_recommendation:
            inc.log_audit("LLM_RECOMMENDATION_LOGGED", f"LLM suggested: '{llm_recommendation}' (Policy Engine authorized: '{policy_dec.action.value}')")

        self.incidents[inc.incident_id] = inc
        self.asset_dedup_index[asset_key] = inc.incident_id
        self.logger.info(f"Created Incident [{inc.incident_id}]: {attack_type} on {affected_asset} ({inc.state.value})")

        return inc

    def transition_state(self, incident_id: str, new_state: IncidentState, actor: str = "ANALYST") -> SecurityIncident:
        """Transitions incident to new lifecycle state."""
        if incident_id not in self.incidents:
            raise KeyError(f"Incident '{incident_id}' not found.")

        inc = self.incidents[incident_id]
        old_state = inc.state
        inc.state = new_state
        inc.log_audit("STATE_TRANSITION", f"State changed from {old_state.value} to {new_state.value}", actor=actor)
        self.logger.info(f"Incident [{incident_id}] state transitioned: {old_state.value} -> {new_state.value}")
        return inc

    def assign_incident(self, incident_id: str, assignee: str) -> SecurityIncident:
        """Assigns incident to a security analyst."""
        if incident_id not in self.incidents:
            raise KeyError(f"Incident '{incident_id}' not found.")

        inc = self.incidents[incident_id]
        inc.assigned_to = assignee
        inc.state = IncidentState.INVESTIGATING
        inc.log_audit("ASSIGNED", f"Assigned to {assignee}", actor="SUPERVISOR")
        return inc

    def resolve_incident(self, incident_id: str, resolution_notes: str, actor: str = "ANALYST") -> SecurityIncident:
        """Resolves incident with resolution notes."""
        if incident_id not in self.incidents:
            raise KeyError(f"Incident '{incident_id}' not found.")

        inc = self.incidents[incident_id]
        inc.resolution_notes = resolution_notes
        inc.state = IncidentState.RESOLVED
        inc.log_audit("RESOLVED", f"Resolved with notes: {resolution_notes}", actor=actor)
        return inc

    def close_incident(self, incident_id: str, actor: str = "ANALYST") -> SecurityIncident:
        """Closes incident permanently."""
        if incident_id not in self.incidents:
            raise KeyError(f"Incident '{incident_id}' not found.")

        inc = self.incidents[incident_id]
        inc.state = IncidentState.CLOSED
        inc.log_audit("CLOSED", "Incident closed.", actor=actor)
        return inc
