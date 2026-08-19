"""
SECUROXI AI Intelligence 2.0 — Enterprise Advanced RBAC, Identity & SSO Test Suite (Stage 37)
Validates granular RBAC permission resolution, bounded agent delegation, SSO assertion verification,
session revocation, and dual RBAC + Policy verification.
"""

import pytest
import time
from securoxi.enterprise.identity import (
    EnterpriseRBACManager,
    Permission,
    IdentityContext,
    DelegationContext,
    SSOProviderConfig,
    SSOAssertion,
    SSOProtocol,
    AuthMethod,
)
from securoxi.enterprise.types import EnterpriseRole


# =========================================================================
# 1. GRANULAR RBAC & DUAL VERIFICATION (RBAC + POLICY)
# =========================================================================

def test_rbac_permission_resolution_and_dual_verification():
    """Verifies that roles grant explicit granular permissions and respect policy dominance."""
    manager = EnterpriseRBACManager()

    # Recruiter has candidate screening permissions, but not security action permissions
    recruiter_ctx = manager.resolve_identity_context(
        user_id="recruiter-bob",
        organization_id="ORG-ACME",
        workspace_id="WS-HIRING",
        roles=["RECRUITER"],
    )

    assert manager.check_access(recruiter_ctx, Permission.CANDIDATE_SCREEN, policy_allowed=True) is True
    assert manager.check_access(recruiter_ctx, Permission.SECURITY_ACTION, policy_allowed=True) is False  # RBAC Deny

    # If RBAC allows but Policy denies -> MUST BE DENIED
    assert manager.check_access(recruiter_ctx, Permission.CANDIDATE_SCREEN, policy_allowed=False) is False  # Policy Deny


# =========================================================================
# 2. BOUNDED AGENT DELEGATION
# =========================================================================

def test_bounded_agent_delegation():
    """Verifies that an agent receives time-bounded delegation and cannot exceed user permissions."""
    manager = EnterpriseRBACManager()

    recruiter_ctx = manager.resolve_identity_context(
        user_id="recruiter-bob",
        organization_id="ORG-ACME",
        workspace_id="WS-HIRING",
        roles=["RECRUITER"],
    )

    # 1. Valid delegation (subset of permissions)
    del_valid = manager.create_delegation(
        user_ctx=recruiter_ctx,
        agent_id="hiring-agent",
        task_id="TASK-SCREEN-01",
        allowed_permissions={Permission.CANDIDATE_READ, Permission.CANDIDATE_SCREEN},
        ttl_seconds=1800,
    )
    assert del_valid is not None
    assert del_valid.is_valid(Permission.CANDIDATE_SCREEN) is True
    assert del_valid.is_valid(Permission.SECURITY_ACTION) is False

    # 2. Invalid delegation (attempting privilege escalation beyond user permissions)
    del_invalid = manager.create_delegation(
        user_ctx=recruiter_ctx,
        agent_id="hiring-agent",
        task_id="TASK-SCREEN-02",
        allowed_permissions={Permission.POLICY_MANAGE},  # Recruiter does not have POLICY_MANAGE
    )
    assert del_invalid is None


# =========================================================================
# 3. ENTERPRISE SSO CONFIGURATION & CLAIM VERIFICATION
# =========================================================================

def test_enterprise_sso_assertion_verification():
    """Verifies SSO provider configuration, domain verification, and IdP group role mapping."""
    manager = EnterpriseRBACManager()

    sso_config = SSOProviderConfig(
        organization_id="ORG-CORP",
        protocol=SSOProtocol.OIDC,
        issuer_url="https://okta.enterprise.com",
        client_id="securoxi-app",
        verified_domains=["enterprise.com"],
        role_mappings={
            "Okta-Securoxi-Admins": EnterpriseRole.ORG_ADMIN.value,
            "Okta-Securoxi-Recruiters": "RECRUITER",
        },
    )
    manager.register_sso_config(sso_config)

    # 1. Valid Assertion
    valid_assertion = SSOAssertion(
        issuer="https://okta.enterprise.com",
        subject_user_id="user-123",
        email="alice@enterprise.com",
        domain="enterprise.com",
        idp_groups=["Okta-Securoxi-Recruiters"],
    )
    roles = manager.verify_sso_assertion("ORG-CORP", valid_assertion)
    assert roles == ["RECRUITER"]

    # 2. Invalid Assertion (unverified domain)
    unverified_domain_assertion = SSOAssertion(
        issuer="https://okta.enterprise.com",
        subject_user_id="user-456",
        email="attacker@untrusted.com",
        domain="untrusted.com",
        idp_groups=["Okta-Securoxi-Admins"],
    )
    assert manager.verify_sso_assertion("ORG-CORP", unverified_domain_assertion) is None


# =========================================================================
# 4. SESSION REVOCATION & EXPIRATION
# =========================================================================

def test_session_revocation():
    """Verifies that revoked sessions immediately lose access."""
    manager = EnterpriseRBACManager()

    ctx = manager.resolve_identity_context(
        user_id="user-alice",
        organization_id="ORG-ACME",
        workspace_id="WS-GEN",
        roles=[EnterpriseRole.ORG_ADMIN.value],
    )

    assert manager.check_access(ctx, Permission.ORG_READ) is True
    manager.revoke_session(ctx.session_id)
    assert manager.check_access(ctx, Permission.ORG_READ) is False
