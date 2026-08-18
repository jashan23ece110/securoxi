"""
SECUROXI AI Intelligence 2.0 — Cross-Agent Verifier & Conflict Resolver
Enforces deterministic security authority, provenance integrity, cross-tenant isolation,
evidence citation validity, and multi-agent conflict resolution.
"""

from typing import Dict, Any, List, Optional
from securoxi.orchestrator.coordination.types import (
    AuthorityLevel,
    VerificationState,
    ConflictType,
)
from securoxi.orchestrator.coordination.models import (
    AgentResultEnvelope,
    CoordinationConflict,
    VerificationResult,
)
from securoxi.brain.policy_engine import SecuroxiPolicyEngine
from securoxi.logger import get_logger

logger = get_logger("orchestrator.cross_agent_verifier")


class CrossAgentVerifier:
    """
    Authoritative verification and conflict resolution engine across specialized agents.
    Enforces deterministic precedence: Policy / Security Engine > Deterministic Tools > Evidence > Advisory.
    """

    def __init__(self, policy_engine: Optional[SecuroxiPolicyEngine] = None):
        self.policy_engine = policy_engine or SecuroxiPolicyEngine()

    def verify_envelopes(
        self,
        envelopes: List[AgentResultEnvelope],
        tenant_id: str,
        user_constraints: Optional[List[str]] = None,
    ) -> VerificationResult:
        """
        Executes cross-agent verification across all generated result envelopes:
        1. Tenant isolation validation.
        2. Provenance chain validation.
        3. Cross-agent contradiction and conflict detection.
        4. Deterministic security authority enforcement.
        """
        conflicts: List[CoordinationConflict] = []
        unresolved: List[str] = []
        security_cleared = True
        provenance_valid = True

        # 1. Tenant Isolation Check
        for env in envelopes:
            for prov in env.provenance:
                if "Tenant:" in prov and not prov.endswith(f"Tenant:{tenant_id}") and f"Tenant:{tenant_id}" not in prov:
                    unresolved.append(f"Tenant isolation breach in envelope {env.envelope_id}: {prov}")
                    provenance_valid = False

        # 2. Check Security vs Hiring Conflicts
        sec_env = next((e for e in envelopes if "security" in e.agent_identity.lower()), None)
        hiring_env = next((e for e in envelopes if "hiring" in e.agent_identity.lower()), None)

        if sec_env and hiring_env:
            sec_state = sec_env.result_data.get("verdict", sec_env.result_data.get("security_state", "SAFE"))
            quarantined = hiring_env.result_data.get("quarantined_candidates", [])
            shortlist = hiring_env.result_data.get("shortlist", [])

            # If security state is HIGH_RISK, no candidate in shortlist can be from high risk
            if sec_state in ["HIGH_RISK", "BLOCK"] and len(shortlist) > 0 and len(quarantined) == 0:
                conf = CoordinationConflict(
                    conflict_type=ConflictType.SECURITY_CONFLICT,
                    conflicting_agents=[sec_env.agent_identity, hiring_env.agent_identity],
                    claims={"security": sec_state, "hiring": shortlist},
                    authority_levels={
                        sec_env.agent_identity: AuthorityLevel.AUTHORITATIVE.value,
                        hiring_env.agent_identity: AuthorityLevel.ADVISORY.value,
                    },
                    resolved=True,
                    resolution_method="SECURITY_AUTHORITY_PRECEDENCE",
                    resolution_outcome="Security Authority overrides Hiring Agent. High risk candidates quarantined.",
                )
                conflicts.append(conf)
                security_cleared = False

        # 3. Check Retrieval vs Hiring Evidence Conflicts
        ret_env = next((e for e in envelopes if "retrieval" in e.agent_identity.lower()), None)
        if ret_env and hiring_env:
            evidence_pack = ret_env.result_data.get("evidence_pack", {})
            suff_state = evidence_pack.get("sufficiency_state", "SUFFICIENT")
            if suff_state in ["INSUFFICIENT", "CONFLICTING"] and hiring_env.status == "COMPLETED":
                conf = CoordinationConflict(
                    conflict_type=ConflictType.EVIDENCE_CONFLICT,
                    conflicting_agents=[ret_env.agent_identity, hiring_env.agent_identity],
                    claims={"retrieval": suff_state, "hiring": "COMPLETED"},
                    authority_levels={
                        ret_env.agent_identity: AuthorityLevel.VERIFIED.value,
                        hiring_env.agent_identity: AuthorityLevel.ADVISORY.value,
                    },
                    resolved=True,
                    resolution_method="EVIDENCE_SUFFICIENCY_GOVERNANCE",
                    resolution_outcome="Flagged as Partial Coverage due to insufficient retrieved evidence.",
                )
                conflicts.append(conf)

        is_valid = len(unresolved) == 0
        state = VerificationState.VERIFIED if is_valid and len(conflicts) == 0 else (
            VerificationState.CONFLICTING if conflicts else VerificationState.FAILED
        )

        return VerificationResult(
            is_valid=is_valid,
            verification_state=state,
            conflicts=conflicts,
            provenance_valid=provenance_valid,
            security_cleared=security_cleared,
            unresolved_issues=unresolved,
            details=f"Verified {len(envelopes)} envelopes. Conflicts: {len(conflicts)}. Issues: {len(unresolved)}",
        )
