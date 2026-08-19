"""
SECUROXI AI Intelligence 2.0 — Enterprise Integration Manager
Coordinates organization-scoped ATS connections, adapter execution, capability discovery,
and governed write operations across Greenhouse, Lever, and Workday.
"""

from typing import Dict, Any, List, Optional
import time
from securoxi.enterprise.integrations.types import (
    ATSProviderType,
    IntegrationStatus,
    IntegrationCapability,
    SyncStatus,
)
from securoxi.enterprise.integrations.models import (
    EnterpriseIntegration,
    ExternalJob,
    ExternalCandidate,
    ATSWriteProposal,
)
from securoxi.enterprise.integrations.adapters import (
    BaseEnterpriseATSAdapter,
    GreenhouseAdapter,
    LeverAdapter,
    WorkdayAdapter,
)
from securoxi.enterprise.identity.models import IdentityContext
from securoxi.enterprise.identity.types import Permission
from securoxi.logger import get_logger

logger = get_logger("enterprise.integrations")


class EnterpriseIntegrationManager:
    """
    Enterprise Integration Manager.
    Enforces multi-organization isolation, adapter capability boundaries, and governed ATS writes.
    """

    def __init__(self):
        self._integrations: Dict[str, EnterpriseIntegration] = {}
        self._adapters: Dict[ATSProviderType, BaseEnterpriseATSAdapter] = {
            ATSProviderType.GREENHOUSE: GreenhouseAdapter(),
            ATSProviderType.LEVER: LeverAdapter(),
            ATSProviderType.WORKDAY: WorkdayAdapter(),
        }
        self._proposals: Dict[str, ATSWriteProposal] = {}

    def connect_integration(
        self,
        organization_id: str,
        provider_type: ATSProviderType,
        workspace_id: Optional[str] = None,
    ) -> EnterpriseIntegration:
        """Provisions a new enterprise ATS integration and performs capability discovery."""
        adapter = self._adapters.get(provider_type)
        capabilities = adapter.capabilities if adapter else set()

        integration = EnterpriseIntegration(
            organization_id=organization_id,
            workspace_id=workspace_id,
            provider_type=provider_type,
            status=IntegrationStatus.CONNECTED,
            capabilities=capabilities,
        )
        self._integrations[integration.integration_id] = integration
        logger.info(f"Connected Integration '{integration.integration_id}' for Org '{organization_id}' ({provider_type.value})")
        return integration

    def list_integrations(self, organization_id: str) -> List[EnterpriseIntegration]:
        """Lists active integrations for a specific organization (enforces tenant isolation)."""
        return [i for i in self._integrations.values() if i.organization_id == organization_id and i.status != IntegrationStatus.DISCONNECTED]

    def fetch_jobs(self, integration_id: str, organization_id: str) -> List[ExternalJob]:
        """Fetches jobs through the provider adapter, ensuring organization boundary matches."""
        if integration_id not in self._integrations:
            return []

        integration = self._integrations[integration_id]
        if integration.organization_id != organization_id:
            logger.warning(f"Cross-Org ATS Access Blocked: Integration '{integration_id}' belongs to Org '{integration.organization_id}', not '{organization_id}'")
            return []

        adapter = self._adapters.get(integration.provider_type)
        if not adapter or IntegrationCapability.READ_JOBS not in integration.capabilities:
            return []

        return adapter.fetch_jobs(integration_id, organization_id)

    def fetch_candidates(self, integration_id: str, organization_id: str, job_id: Optional[str] = None) -> List[ExternalCandidate]:
        """Fetches candidates through the provider adapter with strict organization isolation."""
        if integration_id not in self._integrations:
            return []

        integration = self._integrations[integration_id]
        if integration.organization_id != organization_id:
            logger.warning(f"Cross-Org ATS Access Blocked: Integration '{integration_id}' Org mismatch")
            return []

        adapter = self._adapters.get(integration.provider_type)
        if not adapter or IntegrationCapability.READ_CANDIDATES not in integration.capabilities:
            return []

        return adapter.fetch_candidates(integration_id, organization_id, job_id)

    def propose_ats_write(
        self,
        integration_id: str,
        organization_id: str,
        candidate_id: str,
        target_stage: str,
        user_ctx: IdentityContext,
        policy_allowed: bool = True,
    ) -> Optional[ATSWriteProposal]:
        """
        Creates a governed ATS write proposal requiring explicit permissions and policy authorization.
        """
        if integration_id not in self._integrations:
            return None

        integration = self._integrations[integration_id]
        if integration.organization_id != organization_id or user_ctx.organization_id != organization_id:
            logger.error("ATS Write Blocked: Organization mismatch")
            return None

        if IntegrationCapability.WRITE_STAGE not in integration.capabilities:
            logger.error(f"ATS Write Blocked: Provider '{integration.provider_type.value}' does not support WRITE_STAGE")
            return None

        if not user_ctx.has_permission(Permission.ATS_WRITE) or not policy_allowed:
            logger.error(f"ATS Write Blocked: User '{user_ctx.user_id}' lacks ATS_WRITE permission or Policy denied")
            return None

        proposal = ATSWriteProposal(
            integration_id=integration_id,
            organization_id=organization_id,
            candidate_id=candidate_id,
            target_stage=target_stage,
        )
        self._proposals[proposal.proposal_id] = proposal
        logger.info(f"Created ATS Write Proposal '{proposal.proposal_id}' for Candidate '{candidate_id}' -> Stage '{target_stage}'")
        return proposal

    def approve_and_execute_ats_write(
        self,
        proposal_id: str,
        approver_ctx: IdentityContext,
    ) -> bool:
        """Applies human governance approval and executes the external mutation."""
        if proposal_id not in self._proposals:
            return False

        proposal = self._proposals[proposal_id]
        if approver_ctx.organization_id != proposal.organization_id:
            logger.error("ATS Write Approval Blocked: Approver org mismatch")
            return False

        if not approver_ctx.has_permission(Permission.APPROVAL_APPROVE):
            logger.error(f"ATS Write Approval Blocked: Approver '{approver_ctx.user_id}' lacks APPROVAL_APPROVE permission")
            return False

        integration = self._integrations.get(proposal.integration_id)
        if not integration:
            return False

        adapter = self._adapters.get(integration.provider_type)
        if not adapter:
            return False

        success = adapter.update_candidate_stage(proposal.candidate_id, proposal.target_stage)
        if success:
            proposal.is_approved = True
            proposal.approved_by = approver_ctx.user_id
            proposal.executed = True
            logger.info(f"Executed ATS Write Proposal '{proposal_id}' successfully")
            return True

        return False
