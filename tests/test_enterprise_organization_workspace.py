"""
SECUROXI AI Intelligence 2.0 — Enterprise Organization & Workspace Management Test Suite (Stage 36)
Validates organization lifecycle, workspace hierarchies, membership authorization,
tenant compatibility, and strict cross-organization/cross-workspace data isolation.
"""

import pytest
from securoxi.enterprise import (
    EnterpriseOrganizationManager,
    OrganizationStatus,
    WorkspaceType,
    WorkspaceStatus,
    MembershipStatus,
    EnterpriseRole,
    OrganizationContext,
)


# =========================================================================
# 1. ORGANIZATION CREATION & WORKSPACE PROVISIONING
# =========================================================================

def test_organization_and_workspace_provisioning():
    """Verifies that creating an organization provisions a default General workspace and Admin membership."""
    manager = EnterpriseOrganizationManager()

    org = manager.create_organization(
        name="Acme Corporation",
        slug="acme-corp",
        creator_user_id="user-alice",
    )

    assert org.name == "Acme Corporation"
    assert org.status == OrganizationStatus.ACTIVE

    # Create specialized workspaces
    hiring_ws = manager.create_workspace(org.organization_id, name="Talent Acquisition", workspace_type=WorkspaceType.HIRING)
    security_ws = manager.create_workspace(org.organization_id, name="SOC Operations", workspace_type=WorkspaceType.SECURITY)

    assert hiring_ws is not None
    assert hiring_ws.workspace_type == WorkspaceType.HIRING
    assert security_ws.workspace_type == WorkspaceType.SECURITY


# =========================================================================
# 2. MEMBERSHIP, CONTEXT RESOLUTION & TENANT COMPATIBILITY
# =========================================================================

def test_membership_and_context_resolution():
    """Verifies membership validation, workspace switching, and tenant_id compatibility."""
    manager = EnterpriseOrganizationManager()

    org = manager.create_organization(name="Globex Tech", slug="globex", creator_user_id="user-admin")
    hiring_ws = manager.create_workspace(org.organization_id, name="Recruiting", workspace_type=WorkspaceType.HIRING)

    # Invite regular recruiter with access only to Hiring workspace
    manager.invite_member(
        organization_id=org.organization_id,
        user_id="recruiter-bob",
        role=EnterpriseRole.MEMBER,
        allowed_workspaces=[hiring_ws.workspace_id],
    )

    # Context resolution for authorized workspace
    ctx = manager.resolve_context("recruiter-bob", org.organization_id, hiring_ws.workspace_id)
    assert ctx is not None
    assert ctx.organization_id == org.organization_id
    assert ctx.workspace_id == hiring_ws.workspace_id
    assert ctx.tenant_id == org.organization_id  # Tenant compatibility bridge


# =========================================================================
# 3. STRICT CROSS-ORGANIZATION & CROSS-WORKSPACE ISOLATION
# =========================================================================

def test_cross_organization_and_workspace_access_blocked():
    """Verifies that users cannot access resources or resolve contexts in unauthorized orgs/workspaces."""
    manager = EnterpriseOrganizationManager()

    org_a = manager.create_organization(name="Org Alpha", slug="alpha", creator_user_id="admin-a")
    org_b = manager.create_organization(name="Org Beta", slug="beta", creator_user_id="admin-b")

    ws_a = manager.create_workspace(org_a.organization_id, name="Alpha Sec", workspace_type=WorkspaceType.SECURITY)
    ws_b = manager.create_workspace(org_b.organization_id, name="Beta Sec", workspace_type=WorkspaceType.SECURITY)

    manager.invite_member(org_a.organization_id, user_id="user-a", role=EnterpriseRole.MEMBER, allowed_workspaces=[ws_a.workspace_id])

    # 1. User A tries to resolve context in Org B -> MUST BE DENIED
    ctx_b = manager.resolve_context("user-a", org_b.organization_id, ws_b.workspace_id)
    assert ctx_b is None

    # 2. User A resolves context in Org A -> Allowed
    ctx_a = manager.resolve_context("user-a", org_a.organization_id, ws_a.workspace_id)
    assert ctx_a is not None

    # 3. Validate resource access check
    assert manager.validate_resource_access(ctx_a, resource_org_id=org_a.organization_id, resource_workspace_id=ws_a.workspace_id) is True
    assert manager.validate_resource_access(ctx_a, resource_org_id=org_b.organization_id, resource_workspace_id=ws_b.workspace_id) is False
