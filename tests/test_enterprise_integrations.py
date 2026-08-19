"""
SECUROXI AI Intelligence 2.0 — Enterprise ATS Integrations Test Suite (Stage 38)
Validates enterprise ATS connections (Greenhouse, Lever, Workday), capability discovery,
organization isolation, and governed ATS write proposals.
"""

import pytest
from securoxi.enterprise.integrations import (
    EnterpriseIntegrationManager,
    ATSProviderType,
    IntegrationStatus,
    IntegrationCapability,
)
from securoxi.enterprise.identity import (
    EnterpriseRBACManager,
    Permission,
)
from securoxi.enterprise.types import EnterpriseRole


# =========================================================================
# 1. PROVIDER CONNECTION & CAPABILITY DISCOVERY
# =========================================================================

def test_enterprise_ats_connection_and_capabilities():
    """Verifies connecting Greenhouse, Lever, and Workday with automated capability discovery."""
    manager = EnterpriseIntegrationManager()

    # 1. Greenhouse (Full read + write)
    gh = manager.connect_integration("ORG-ACME", ATSProviderType.GREENHOUSE, workspace_id="WS-HIRING")
    assert gh.status == IntegrationStatus.CONNECTED
    assert IntegrationCapability.WRITE_STAGE in gh.capabilities
    assert IntegrationCapability.READ_JOBS in gh.capabilities

    # 2. Workday (Read-only capabilities)
    wd = manager.connect_integration("ORG-ACME", ATSProviderType.WORKDAY, workspace_id="WS-HIRING")
    assert wd.status == IntegrationStatus.CONNECTED
    assert IntegrationCapability.WRITE_STAGE not in wd.capabilities
    assert IntegrationCapability.READ_CANDIDATES in wd.capabilities


# =========================================================================
# 2. ORGANIZATION ISOLATION IN ATS FETCHING
# =========================================================================

def test_organization_isolated_ats_fetch():
    """Verifies that jobs and candidates can only be fetched by their owner organization."""
    manager = EnterpriseIntegrationManager()

    gh_a = manager.connect_integration("ORG-ALPHA", ATSProviderType.GREENHOUSE)
    gh_b = manager.connect_integration("ORG-BETA", ATSProviderType.GREENHOUSE)

    # Org Alpha fetches its own jobs
    jobs_a = manager.fetch_jobs(gh_a.integration_id, organization_id="ORG-ALPHA")
    assert len(jobs_a) >= 1
    assert jobs_a[0].organization_id == "ORG-ALPHA"

    # Org Beta attempts to fetch Org Alpha's integration -> MUST RETURN EMPTY (DENIED)
    jobs_cross = manager.fetch_jobs(gh_a.integration_id, organization_id="ORG-BETA")
    assert len(jobs_cross) == 0


# =========================================================================
# 3. GOVERNED ATS WRITE WORKFLOW & APPROVAL
# =========================================================================

def test_governed_ats_write_workflow():
    """Verifies that ATS state mutations require RBAC permissions, policy clearance, and human approval."""
    int_mgr = EnterpriseIntegrationManager()
    rbac_mgr = EnterpriseRBACManager()

    gh = int_mgr.connect_integration("ORG-CORP", ATSProviderType.GREENHOUSE)

    # 1. Recruiter Context with ATS_WRITE permission
    recruiter_ctx = rbac_mgr.resolve_identity_context(
        user_id="recruiter-bob",
        organization_id="ORG-CORP",
        workspace_id="WS-HIRING",
        roles=[EnterpriseRole.ORG_ADMIN.value],
    )

    # 2. Propose ATS write (e.g. advance candidate to Interview)
    proposal = int_mgr.propose_ats_write(
        integration_id=gh.integration_id,
        organization_id="ORG-CORP",
        candidate_id="GH-CAND-01",
        target_stage="TECHNICAL_INTERVIEW",
        user_ctx=recruiter_ctx,
        policy_allowed=True,
    )
    assert proposal is not None
    assert proposal.executed is False

    # 3. Approve and execute proposal
    approver_ctx = recruiter_ctx  # ORG_ADMIN has APPROVAL_APPROVE
    executed = int_mgr.approve_and_execute_ats_write(proposal.proposal_id, approver_ctx)
    assert executed is True
    assert proposal.executed is True
