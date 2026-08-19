"""
SECUROXI AI Intelligence 2.0 — Enterprise RBAC & Identity Manager
Enforces granular role-to-permission mapping, bounded agent delegation, SSO assertion verification,
session revocation, and dual RBAC + Policy verification.
"""

from typing import Dict, Any, List, Set, Optional
import time
from securoxi.enterprise.identity.types import (
    Permission,
    SSOProtocol,
    AuthMethod,
    DelegationScope,
)
from securoxi.enterprise.identity.models import (
    IdentityContext,
    DelegationContext,
    SSOProviderConfig,
    SSOAssertion,
)
from securoxi.enterprise.types import EnterpriseRole
from securoxi.logger import get_logger

logger = get_logger("enterprise.rbac")


# Canonical Role to Permission Mapping
DEFAULT_ROLE_PERMISSIONS: Dict[str, Set[Permission]] = {
    EnterpriseRole.ORG_ADMIN.value: {
        Permission.ORG_READ, Permission.ORG_UPDATE,
        Permission.MEMBER_READ, Permission.MEMBER_INVITE, Permission.MEMBER_REMOVE,
        Permission.SSO_MANAGE, Permission.WS_READ, Permission.WS_UPDATE, Permission.WS_MANAGE,
        Permission.CANDIDATE_READ, Permission.CANDIDATE_SCREEN, Permission.CANDIDATE_EXPORT,
        Permission.ATS_READ, Permission.ATS_WRITE,
        Permission.INVESTIGATION_READ, Permission.INVESTIGATION_CREATE,
        Permission.INCIDENT_READ, Permission.INCIDENT_UPDATE, Permission.EVIDENCE_READ, Permission.SECURITY_ACTION,
        Permission.APPROVAL_READ, Permission.APPROVAL_APPROVE, Permission.APPROVAL_REJECT,
        Permission.AUDIT_READ, Permission.POLICY_MANAGE,
    },
    EnterpriseRole.WORKSPACE_ADMIN.value: {
        Permission.WS_READ, Permission.WS_UPDATE,
        Permission.CANDIDATE_READ, Permission.CANDIDATE_SCREEN, Permission.CANDIDATE_EXPORT,
        Permission.ATS_READ, Permission.ATS_WRITE,
        Permission.INVESTIGATION_READ, Permission.INVESTIGATION_CREATE,
        Permission.INCIDENT_READ, Permission.EVIDENCE_READ,
        Permission.APPROVAL_READ,
    },
    EnterpriseRole.MEMBER.value: {
        Permission.WS_READ,
        Permission.CANDIDATE_READ, Permission.CANDIDATE_SCREEN,
        Permission.INVESTIGATION_READ, Permission.EVIDENCE_READ,
        Permission.APPROVAL_READ,
    },
    EnterpriseRole.GUEST.value: {
        Permission.WS_READ,
        Permission.CANDIDATE_READ,
        Permission.INVESTIGATION_READ,
    },
    "RECRUITER": {
        Permission.WS_READ,
        Permission.CANDIDATE_READ, Permission.CANDIDATE_SCREEN, Permission.CANDIDATE_EXPORT,
        Permission.ATS_READ,
    },
    "SECURITY_ANALYST": {
        Permission.WS_READ,
        Permission.INVESTIGATION_READ, Permission.INVESTIGATION_CREATE,
        Permission.INCIDENT_READ, Permission.INCIDENT_UPDATE, Permission.EVIDENCE_READ, Permission.SECURITY_ACTION,
    },
    "AUDITOR": {
        Permission.WS_READ,
        Permission.AUDIT_READ,
        Permission.EVIDENCE_READ,
    },
}


class EnterpriseRBACManager:
    """
    Enterprise RBAC & Identity Authorization Engine.
    Coordinates permission resolution, agent delegation, session tracking, and SSO assertion validation.
    """

    def __init__(self, role_permissions: Optional[Dict[str, Set[Permission]]] = None):
        self.role_permissions = role_permissions or DEFAULT_ROLE_PERMISSIONS
        self._revoked_sessions: Set[str] = set()
        self._sso_configs: Dict[str, SSOProviderConfig] = {}
        self._delegations: Dict[str, DelegationContext] = {}

    def register_sso_config(self, config: SSOProviderConfig) -> str:
        """Registers an enterprise SSO identity provider configuration."""
        self._sso_configs[config.organization_id] = config
        logger.info(f"Registered SSO provider '{config.idp_id}' for Organization '{config.organization_id}' (Issuer: {config.issuer_url})")
        return config.idp_id

    def resolve_identity_context(
        self,
        user_id: str,
        organization_id: str,
        workspace_id: str,
        roles: List[str],
        membership_id: str = "MEM-DEFAULT",
        auth_method: AuthMethod = AuthMethod.LOCAL_PASSWORD,
    ) -> IdentityContext:
        """Resolves active permissions for a user given their roles within an organization and workspace."""
        all_permissions: Set[Permission] = set()
        for role in roles:
            if role in self.role_permissions:
                all_permissions.update(self.role_permissions[role])

        return IdentityContext(
            user_id=user_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            membership_id=membership_id,
            roles=roles,
            permissions=all_permissions,
            auth_method=auth_method,
        )

    def create_delegation(
        self,
        user_ctx: IdentityContext,
        agent_id: str,
        task_id: str,
        allowed_permissions: Set[Permission],
        ttl_seconds: int = 3600,
    ) -> Optional[DelegationContext]:
        """
        Creates a time-bounded, scoped delegation for an agent to execute on behalf of a user.
        The agent can only receive a subset of the delegating user's actual permissions.
        """
        # Invariant: Agent cannot be granted permissions the user does not have
        unauthorized = allowed_permissions - user_ctx.permissions
        if unauthorized:
            logger.error(f"Delegation Denied: User '{user_ctx.user_id}' lacks requested permissions {[p.value for p in unauthorized]}")
            return None

        delegation = DelegationContext(
            delegating_user_id=user_ctx.user_id,
            delegated_agent_id=agent_id,
            organization_id=user_ctx.organization_id,
            workspace_id=user_ctx.workspace_id,
            scope=DelegationScope.TASK_BOUNDED,
            allowed_permissions=allowed_permissions,
            task_id=task_id,
            expires_at=time.time() + ttl_seconds,
        )
        self._delegations[delegation.delegation_id] = delegation
        logger.info(f"Created Agent Delegation '{delegation.delegation_id}' for Agent '{agent_id}' on Task '{task_id}'")
        return delegation

    def verify_sso_assertion(
        self,
        organization_id: str,
        assertion: SSOAssertion,
    ) -> Optional[List[str]]:
        """
        Validates an incoming SSO assertion against the organization's SSO configuration.
        Returns mapped roles if valid, or None if rejected.
        """
        if organization_id not in self._sso_configs:
            logger.warning(f"SSO Rejected: No SSO config found for Organization '{organization_id}'")
            return None

        config = self._sso_configs[organization_id]
        if not config.is_active:
            logger.warning(f"SSO Rejected: SSO config for Organization '{organization_id}' is inactive")
            return None

        # 1. Issuer Validation
        if assertion.issuer != config.issuer_url:
            logger.warning(f"SSO Rejected: Issuer mismatch ({assertion.issuer} != {config.issuer_url})")
            return None

        # 2. Expiration Validation
        if time.time() > assertion.expires_at:
            logger.warning(f"SSO Rejected: Assertion expired")
            return None

        # 3. Domain Verification
        if config.verified_domains and assertion.domain not in config.verified_domains:
            logger.warning(f"SSO Rejected: Domain '{assertion.domain}' not verified for Organization '{organization_id}'")
            return None

        # Map IDP groups to SECUROXI roles
        resolved_roles: List[str] = []
        for group in assertion.idp_groups:
            if group in config.role_mappings:
                resolved_roles.append(config.role_mappings[group])

        if not resolved_roles:
            resolved_roles = [EnterpriseRole.MEMBER.value]

        return resolved_roles

    def revoke_session(self, session_id: str):
        """Immediately revokes an active session ID."""
        self._revoked_sessions.add(session_id)
        logger.info(f"Revoked session '{session_id}'")

    def is_session_revoked(self, session_id: str) -> bool:
        return session_id in self._revoked_sessions

    def check_access(
        self,
        identity_ctx: IdentityContext,
        required_permission: Permission,
        policy_allowed: bool = True,
    ) -> bool:
        """
        Enforces Dual Verification:
        1. Session must not be revoked or expired.
        2. RBAC must grant permission (deny-by-default).
        3. Deterministic Policy must ALLOW (policy dominance).
        """
        if self.is_session_revoked(identity_ctx.session_id) or identity_ctx.is_expired():
            logger.warning(f"Access Denied: Session '{identity_ctx.session_id}' is revoked or expired")
            return False

        if not identity_ctx.has_permission(required_permission):
            logger.warning(f"Access Denied: User '{identity_ctx.user_id}' lacks permission '{required_permission.value}'")
            return False

        if not policy_allowed:
            logger.warning(f"Access Denied: Deterministic Security Policy denied action for '{identity_ctx.user_id}'")
            return False

        return True
