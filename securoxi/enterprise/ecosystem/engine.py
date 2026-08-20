"""
SECUROXI AI Intelligence 2.0 — Enterprise Partner Ecosystem Engine (Phase 9 Stage 60)
Governs partner registration, identity verification, explicit customer delegations,
granular scope enforcement, and complete partner offboarding.
"""

from typing import Dict, Any, List, Optional
import time
from securoxi.enterprise.ecosystem.types import (
    PartnerType,
    PartnerVerificationStatus,
    DelegationStatus,
    PartnerScope,
)
from securoxi.enterprise.ecosystem.models import (
    PartnerOrganization,
    CustomerDelegation,
    PartnerApplication,
)
from securoxi.logger import get_logger

logger = get_logger("enterprise.ecosystem.engine")


class EnterprisePartnerEcosystemEngine:
    """
    Enterprise Extensibility, Ecosystem & Partner Platform Engine.
    Enforces identity verification, customer consent delegations, tenant isolation,
    scoped access permissions, and automated partner offboarding.
    """

    def __init__(self):
        self._partners: Dict[str, PartnerOrganization] = {}            # partner_id -> PartnerOrganization
        self._delegations: Dict[str, CustomerDelegation] = {}          # delegation_id -> CustomerDelegation
        self._applications: Dict[str, PartnerApplication] = {}        # app_id -> PartnerApplication

    def register_partner(
        self,
        name: str,
        partner_type: PartnerType = PartnerType.INTEGRATION_PARTNER,
        allowed_scopes: Optional[List[PartnerScope]] = None,
    ) -> PartnerOrganization:
        """Registers a new partner organization in UNVERIFIED status."""
        partner = PartnerOrganization(
            name=name,
            partner_type=partner_type,
            verification_status=PartnerVerificationStatus.UNVERIFIED,
            allowed_scopes=allowed_scopes or [PartnerScope.API_READ],
        )
        self._partners[partner.partner_id] = partner
        logger.info(f"Registered Partner '{partner.partner_id}' ('{name}') Status=UNVERIFIED")
        return partner

    def verify_partner(self, partner_id: str, status: PartnerVerificationStatus) -> bool:
        """Updates partner verification status (VERIFIED, APPROVED, SUSPENDED, REVOKED)."""
        partner = self._partners.get(partner_id)
        if not partner:
            return False

        partner.verification_status = status
        partner.updated_at = time.time()
        logger.info(f"Updated Partner '{partner_id}' verification status to '{status.value}'")
        return True

    def create_customer_delegation(
        self,
        customer_organization_id: str,
        partner_id: str,
        allowed_workspaces: Optional[List[str]] = None,
        granted_scopes: Optional[List[PartnerScope]] = None,
        duration_seconds: float = 86400.0,
    ) -> CustomerDelegation:
        """
        Creates an explicit, scoped delegation from an enterprise customer to a partner.
        """
        partner = self._partners.get(partner_id)
        if not partner or partner.verification_status not in {PartnerVerificationStatus.VERIFIED, PartnerVerificationStatus.APPROVED}:
            raise ValueError(f"Cannot delegate to unverified partner '{partner_id}'")

        delegation = CustomerDelegation(
            customer_organization_id=customer_organization_id,
            partner_id=partner_id,
            allowed_workspaces=allowed_workspaces or ["*"],
            granted_scopes=granted_scopes or [PartnerScope.API_READ],
            status=DelegationStatus.ACTIVE,
            expires_at=time.time() + duration_seconds,
        )
        self._delegations[delegation.delegation_id] = delegation
        logger.info(f"Created Customer Delegation '{delegation.delegation_id}' from Org '{customer_organization_id}' to Partner '{partner_id}'")
        return delegation

    def revoke_delegation(self, customer_organization_id: str, delegation_id: str) -> bool:
        """Revokes an existing customer delegation."""
        delegation = self._delegations.get(delegation_id)
        if not delegation or delegation.customer_organization_id != customer_organization_id:
            return False

        delegation.status = DelegationStatus.REVOKED
        logger.info(f"Revoked Customer Delegation '{delegation_id}' for Org '{customer_organization_id}'")
        return True

    def validate_partner_access(
        self,
        partner_id: str,
        target_customer_org_id: str,
        workspace_id: str,
        requested_scope: PartnerScope,
    ) -> Dict[str, Any]:
        """
        Validates partner authorization against customer delegation, scopes, and expiration.
        """
        # 1. Partner Verification Gate
        partner = self._partners.get(partner_id)
        if not partner or partner.verification_status not in {PartnerVerificationStatus.VERIFIED, PartnerVerificationStatus.APPROVED}:
            return {"authorized": False, "error": "PARTNER_NOT_VERIFIED"}

        # 2. Delegation Lookup
        active_delegations = [
            d for d in self._delegations.values()
            if d.partner_id == partner_id
            and d.customer_organization_id == target_customer_org_id
            and d.status == DelegationStatus.ACTIVE
        ]

        if not active_delegations:
            logger.error(f"Cross-Tenant Access DENIED: Partner '{partner_id}' has no active delegation from Org '{target_customer_org_id}'")
            return {"authorized": False, "error": "DELEGATION_NOT_FOUND"}

        delegation = active_delegations[0]

        # 3. Expiration Check
        if time.time() > delegation.expires_at:
            delegation.status = DelegationStatus.EXPIRED
            logger.warning(f"Delegation '{delegation.delegation_id}' expired at {delegation.expires_at}")
            return {"authorized": False, "error": "DELEGATION_EXPIRED"}

        # 4. Workspace Scope Check
        if "*" not in delegation.allowed_workspaces and workspace_id not in delegation.allowed_workspaces:
            logger.warning(f"Delegation '{delegation.delegation_id}' does not cover workspace '{workspace_id}'")
            return {"authorized": False, "error": "WORKSPACE_NOT_PERMITTED"}

        # 5. Granular Scope Check
        if requested_scope not in delegation.granted_scopes:
            logger.warning(f"Delegation '{delegation.delegation_id}' does not grant requested scope '{requested_scope.value}'")
            return {"authorized": False, "error": "SCOPE_NOT_GRANTED"}

        return {"authorized": True, "delegation_id": delegation.delegation_id}

    def offboard_partner(self, partner_id: str):
        """
        Offboards a partner: revokes status and immediately terminates all active customer delegations.
        """
        partner = self._partners.get(partner_id)
        if not partner:
            return

        partner.verification_status = PartnerVerificationStatus.REVOKED
        logger.warning(f"OFFBOARDING PARTNER: Partner '{partner_id}' status set to REVOKED")

        # Revoke all active delegations for this partner
        for delegation in self._delegations.values():
            if delegation.partner_id == partner_id and delegation.status == DelegationStatus.ACTIVE:
                delegation.status = DelegationStatus.REVOKED
                logger.info(f"Terminated delegation '{delegation.delegation_id}' due to partner offboarding")
