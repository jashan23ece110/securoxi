"""
SECUROXI AI Intelligence 2.0 — Enterprise Partner Ecosystem Test Suite (Phase 9 Stage 60)
Validates partner registration, verification, customer consent delegations,
scoped access validation, cross-tenant isolation, and complete partner offboarding.
"""

import pytest
from securoxi.enterprise.ecosystem import (
    EnterprisePartnerEcosystemEngine,
    PartnerType,
    PartnerVerificationStatus,
    PartnerScope,
)


# =========================================================================
# 1. PARTNER REGISTRATION, VERIFICATION & DELEGATION
# =========================================================================

def test_partner_registration_and_delegation():
    """Verifies partner lifecycle and explicit customer delegation."""
    eco = EnterprisePartnerEcosystemEngine()

    # 1. Register Partner -> UNVERIFIED
    partner = eco.register_partner(name="Acme Solutions", partner_type=PartnerType.INTEGRATION_PARTNER)
    assert partner.verification_status == PartnerVerificationStatus.UNVERIFIED

    # Delegation to unverified partner fails
    with pytest.raises(ValueError, match="Cannot delegate to unverified partner"):
        eco.create_customer_delegation("ORG-CUSTOMER", partner.partner_id)

    # 2. Verify Partner -> VERIFIED
    assert eco.verify_partner(partner.partner_id, PartnerVerificationStatus.VERIFIED) is True

    # 3. Customer creates explicit scoped delegation
    delegation = eco.create_customer_delegation(
        customer_organization_id="ORG-CUSTOMER",
        partner_id=partner.partner_id,
        allowed_workspaces=["WS-PROD"],
        granted_scopes=[PartnerScope.API_READ, PartnerScope.WORKFLOW_READ],
    )
    assert delegation.status.value == "ACTIVE"


# =========================================================================
# 2. SCOPED ACCESS VALIDATION & CROSS-TENANT ISOLATION
# =========================================================================

def test_scoped_access_and_cross_tenant_isolation():
    """Verifies granular scope enforcement, workspace boundaries, and cross-tenant access rejection."""
    eco = EnterprisePartnerEcosystemEngine()

    partner = eco.register_partner(name="Global Integrators", partner_type=PartnerType.TECHNOLOGY_PARTNER)
    eco.verify_partner(partner.partner_id, PartnerVerificationStatus.APPROVED)

    # Customer Alpha delegates WS-ALPHA with API_READ only
    eco.create_customer_delegation(
        customer_organization_id="ORG-ALPHA",
        partner_id=partner.partner_id,
        allowed_workspaces=["WS-ALPHA"],
        granted_scopes=[PartnerScope.API_READ],
    )

    # 1. Valid Access -> Authorized
    res_valid = eco.validate_partner_access(partner.partner_id, "ORG-ALPHA", "WS-ALPHA", PartnerScope.API_READ)
    assert res_valid["authorized"] is True

    # 2. Ungranted Scope (API_WRITE) -> SCOPE_NOT_GRANTED
    res_scope_denied = eco.validate_partner_access(partner.partner_id, "ORG-ALPHA", "WS-ALPHA", PartnerScope.API_WRITE)
    assert res_scope_denied["authorized"] is False
    assert res_scope_denied["error"] == "SCOPE_NOT_GRANTED"

    # 3. Disallowed Workspace (WS-SECRET) -> WORKSPACE_NOT_PERMITTED
    res_ws_denied = eco.validate_partner_access(partner.partner_id, "ORG-ALPHA", "WS-SECRET", PartnerScope.API_READ)
    assert res_ws_denied["authorized"] is False
    assert res_ws_denied["error"] == "WORKSPACE_NOT_PERMITTED"

    # 4. Cross-Tenant Access to Org Beta (No delegation) -> DELEGATION_NOT_FOUND
    res_cross_tenant = eco.validate_partner_access(partner.partner_id, "ORG-BETA", "WS-BETA", PartnerScope.API_READ)
    assert res_cross_tenant["authorized"] is False
    assert res_cross_tenant["error"] == "DELEGATION_NOT_FOUND"


# =========================================================================
# 3. PARTNER OFFBOARDING & DELEGATION TERMINATION
# =========================================================================

def test_partner_offboarding():
    """Verifies that offboarding a partner revokes verification and terminates all customer delegations."""
    eco = EnterprisePartnerEcosystemEngine()

    partner = eco.register_partner(name="Deprecated Partner", partner_type=PartnerType.SOLUTION_PARTNER)
    eco.verify_partner(partner.partner_id, PartnerVerificationStatus.VERIFIED)

    del_1 = eco.create_customer_delegation("ORG-1", partner.partner_id, granted_scopes=[PartnerScope.API_READ])
    del_2 = eco.create_customer_delegation("ORG-2", partner.partner_id, granted_scopes=[PartnerScope.API_READ])

    assert del_1.status.value == "ACTIVE"
    assert del_2.status.value == "ACTIVE"

    # Offboard partner
    eco.offboard_partner(partner.partner_id)
    assert partner.verification_status == PartnerVerificationStatus.REVOKED

    # Delegations terminated
    assert del_1.status.value == "REVOKED"
    assert del_2.status.value == "REVOKED"

    # Subsequent access attempt -> PARTNER_NOT_VERIFIED
    res = eco.validate_partner_access(partner.partner_id, "ORG-1", "WS-DEFAULT", PartnerScope.API_READ)
    assert res["authorized"] is False
    assert res["error"] == "PARTNER_NOT_VERIFIED"
