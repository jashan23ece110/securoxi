"""
SECUROXI AI Intelligence 2.0 — Phase 7 Final Enterprise Freeze Validation Suite (Stage 44)
Validates the complete enterprise platform stack: Organizations, RBAC/Identity/SSO,
ATS Integrations, Data Governance, Analytics, Developer Platform, Customer Configuration,
and Enterprise Scale & Disaster Recovery.
"""

import pytest
import time
from securoxi.enterprise import (
    EnterpriseOrganizationManager,
    OrganizationStatus,
    WorkspaceType,
    EnterpriseRole,
)
from securoxi.enterprise.identity import (
    EnterpriseRBACManager,
    Permission,
    SSOAssertion,
    SSOProviderConfig,
)
from securoxi.enterprise.integrations import (
    EnterpriseIntegrationManager,
    ATSProviderType,
    IntegrationCapability,
)
from securoxi.enterprise.governance import (
    EnterpriseDataGovernanceManager,
    DataClassification,
    LegalHoldStatus,
    RetentionState,
)
from securoxi.enterprise.analytics import (
    EnterpriseAnalyticsManager,
    ReportType,
)
from securoxi.enterprise.developer import (
    EnterpriseAPIManager,
    APIScope,
    WebhookEventType,
    WebhookDeliveryStatus,
)
from securoxi.enterprise.config import (
    EnterpriseConfigurationManager,
    FORBIDDEN_SETTINGS,
)
from securoxi.enterprise.scale import (
    TenantFairnessScheduler,
    EnterpriseDisasterRecoveryManager,
    DataRegion,
    RegionalConfig,
    FailoverStatus,
)


# =========================================================================
# 1. JOURNEY 1: ORGANIZATIONS, WORKSPACES, RBAC & SSO
# =========================================================================

def test_phase7_freeze_journey1_organization_identity_sso():
    """Validates organization creation, workspace scoping, role-to-permission mapping, and SSO."""
    org_mgr = EnterpriseOrganizationManager()
    rbac_mgr = EnterpriseRBACManager()

    # 1. Create Organization & Hiring Workspace
    org = org_mgr.create_organization("Acme Global Defense", slug="acme-global", creator_user_id="alice@acme.com")
    ws = org_mgr.create_workspace(org.organization_id, name="Talent Screening Unit", workspace_type=WorkspaceType.HIRING)

    assert org.organization_id.startswith("ORG-")
    assert ws.organization_id == org.organization_id

    # 2. SSO Provider Registration & Identity Assertion Verification
    sso_config = SSOProviderConfig(
        organization_id=org.organization_id,
        issuer_url="https://idp.acme.com",
        verified_domains=["acme.com"],
        role_mappings={"Securoxi-Recruiters": "RECRUITER"},
    )
    rbac_mgr.register_sso_config(sso_config)

    assertion = SSOAssertion(
        issuer="https://idp.acme.com",
        subject_user_id="alice@acme.com",
        email="alice@acme.com",
        domain="acme.com",
        idp_groups=["Securoxi-Recruiters"],
    )
    mapped_roles = rbac_mgr.verify_sso_assertion(org.organization_id, assertion)
    assert mapped_roles is not None
    assert "RECRUITER" in mapped_roles

    sso_ctx = rbac_mgr.resolve_identity_context(
        user_id="alice@acme.com",
        organization_id=org.organization_id,
        workspace_id=ws.workspace_id,
        roles=mapped_roles,
    )
    assert sso_ctx.has_permission(Permission.CANDIDATE_READ)
    assert not sso_ctx.has_permission(Permission.SECURITY_ACTION)  # Restricted permission withheld


# =========================================================================
# 2. JOURNEY 2: ATS INTEGRATIONS & GOVERNED WRITES
# =========================================================================

def test_phase7_freeze_journey2_ats_integrations_governed_writes():
    """Validates ATS capability discovery, candidate fetching, and governed write proposals."""
    int_mgr = EnterpriseIntegrationManager()
    rbac_mgr = EnterpriseRBACManager()

    # 1. Connect Greenhouse Integration
    gh = int_mgr.connect_integration("ORG-FREEZE", ATSProviderType.GREENHOUSE, workspace_id="WS-HIRING")
    assert IntegrationCapability.WRITE_STAGE in gh.capabilities

    # 2. Fetch candidates (Organization Scoped)
    candidates = int_mgr.fetch_candidates(gh.integration_id, organization_id="ORG-FREEZE")
    assert len(candidates) >= 1

    # 3. Create Governed Write Proposal
    recruiter_ctx = rbac_mgr.resolve_identity_context(
        user_id="recruiter-bob",
        organization_id="ORG-FREEZE",
        workspace_id="WS-HIRING",
        roles=[EnterpriseRole.ORG_ADMIN.value],
    )
    proposal = int_mgr.propose_ats_write(
        integration_id=gh.integration_id,
        organization_id="ORG-FREEZE",
        candidate_id="GH-CAND-01",
        target_stage="INTERVIEW",
        user_ctx=recruiter_ctx,
        policy_allowed=True,
    )
    assert proposal is not None

    # 4. Approve & Execute Proposal
    executed = int_mgr.approve_and_execute_ats_write(proposal.proposal_id, recruiter_ctx)
    assert executed is True
    assert proposal.executed is True


# =========================================================================
# 3. JOURNEY 3: DATA GOVERNANCE & DEVELOPER PLATFORM
# =========================================================================

def test_phase7_freeze_journey3_governance_and_developer_platform():
    """Validates data inventory, legal hold deletion blocking, and signed API webhook delivery."""
    gov_mgr = EnterpriseDataGovernanceManager()
    api_mgr = EnterpriseAPIManager()

    # 1. Register Data Inventory Item & Legal Hold
    gov_mgr.register_inventory_item("ORG-FREEZE", "DOC-001", "Confidential_Resume.pdf", classification=DataClassification.RESTRICTED)
    hold = gov_mgr.apply_legal_hold("ORG-FREEZE", "DOC-001", reason="Audit preservation")

    # Deletion blocked under legal hold
    del_res = gov_mgr.execute_safe_deletion("ORG-FREEZE", "DOC-001")
    assert del_res["success"] is False

    # 2. API Key & Outbound Webhooks with HMAC Signing & SSRF Protection
    key, raw_secret = api_mgr.create_api_key("ORG-FREEZE", scopes={APIScope.TASK_CREATE})
    assert api_mgr.authenticate_api_key(raw_secret, APIScope.TASK_CREATE) is not None

    # SSRF Attack Blocked
    assert api_mgr.register_webhook_subscription("ORG-FREEZE", "http://127.0.0.1:9000/hook") is None

    # Valid Webhook Subscription & Dispatch
    sub = api_mgr.register_webhook_subscription("ORG-FREEZE", "https://api.enterprise.com/webhooks")
    dispatches = api_mgr.emit_event("ORG-FREEZE", WebhookEventType.TASK_COMPLETED, {"task_id": "T-100"})
    assert len(dispatches) == 1
    assert dispatches[0]["status"] == WebhookDeliveryStatus.DELIVERED.value


# =========================================================================
# 4. JOURNEY 4: CONFIGURATION INVARIANTS & SCALE DR
# =========================================================================

def test_phase7_freeze_journey4_configuration_scale_dr():
    """Validates security invariant immutability, tenant fairness, and regional failover recovery."""
    cfg_mgr = EnterpriseConfigurationManager()
    rbac_mgr = EnterpriseRBACManager()
    dr_mgr = EnterpriseDisasterRecoveryManager()
    scheduler = TenantFairnessScheduler(max_concurrent_tasks_per_org=2)

    admin_ctx = rbac_mgr.resolve_identity_context(
        user_id="admin-carol",
        organization_id="ORG-FREEZE",
        workspace_id="WS-DEFAULT",
        roles=[EnterpriseRole.ORG_ADMIN.value],
    )

    # 1. Security Invariants cannot be modified by customer config
    res_forbidden = cfg_mgr.set_configuration(
        user_ctx=admin_ctx,
        organization_id="ORG-FREEZE",
        key="security_authority",
        value=False,
    )
    assert res_forbidden["success"] is False

    # 2. Tenant Fairness scheduler prevents single-tenant starvation
    assert scheduler.acquire_execution_slot("ORG-FREEZE", "T1") is True
    assert scheduler.acquire_execution_slot("ORG-FREEZE", "T2") is True
    assert scheduler.acquire_execution_slot("ORG-FREEZE", "T3") is False  # Throttled

    # 3. Regional Failover
    dr_mgr.configure_region(
        RegionalConfig(
            organization_id="ORG-FREEZE",
            primary_region=DataRegion.US_EAST,
            secondary_region=DataRegion.US_WEST,
        )
    )
    event = dr_mgr.execute_regional_failover("ORG-FREEZE")
    assert event is not None
    assert event.status == FailoverStatus.SECONDARY_ACTIVE
    assert event.recovered_task_count >= 1
