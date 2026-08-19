"""
SECUROXI AI Intelligence 2.0 — Advanced Enterprise RBAC, Identity & SSO Models
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Set, Optional
import time
import uuid
from securoxi.enterprise.identity.types import (
    Permission,
    SSOProtocol,
    AuthMethod,
    DelegationScope,
)
from securoxi.enterprise.types import EnterpriseRole


@dataclass
class IdentityContext:
    """Canonical Identity Context carrying user/service identity, memberships, and permissions."""
    user_id: str
    organization_id: str
    workspace_id: str
    membership_id: str
    roles: List[str] = field(default_factory=lambda: [EnterpriseRole.MEMBER.value])
    permissions: Set[Permission] = field(default_factory=set)
    auth_method: AuthMethod = AuthMethod.LOCAL_PASSWORD
    session_id: str = field(default_factory=lambda: f"SESS-{uuid.uuid4().hex[:12].upper()}")
    is_service_account: bool = False
    issued_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 86400)  # 24h default

    def has_permission(self, permission: Permission) -> bool:
        """Deny-by-default permission check."""
        return permission in self.permissions

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "membership_id": self.membership_id,
            "roles": self.roles,
            "permissions": [p.value for p in self.permissions],
            "auth_method": self.auth_method.value,
            "session_id": self.session_id,
            "is_service_account": self.is_service_account,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
        }


@dataclass
class DelegationContext:
    """Bounded, time-limited delegation allowing agents/tools to execute on behalf of a user."""
    delegation_id: str = field(default_factory=lambda: f"DEL-{uuid.uuid4().hex[:8].upper()}")
    delegating_user_id: str = "USER-DEFAULT"
    delegated_agent_id: str = "AGENT-DEFAULT"
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-DEFAULT"
    scope: DelegationScope = DelegationScope.TASK_BOUNDED
    allowed_permissions: Set[Permission] = field(default_factory=set)
    task_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 3600)  # 1h TTL

    def is_valid(self, permission: Permission) -> bool:
        if time.time() > self.expires_at:
            return False
        return permission in self.allowed_permissions


@dataclass
class SSOProviderConfig:
    """Enterprise SSO Identity Provider configuration for an organization."""
    idp_id: str = field(default_factory=lambda: f"IDP-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    protocol: SSOProtocol = SSOProtocol.OIDC
    issuer_url: str = "https://identity.enterprise.com"
    client_id: str = "securoxi-client"
    verified_domains: List[str] = field(default_factory=list)
    role_mappings: Dict[str, str] = field(default_factory=dict)
    is_active: bool = True
    created_at: float = field(default_factory=time.time)


@dataclass
class SSOAssertion:
    """Verified claims received from an Enterprise SSO provider."""
    assertion_id: str = field(default_factory=lambda: f"ASSERT-{uuid.uuid4().hex[:8].upper()}")
    issuer: str = ""
    subject_user_id: str = ""
    email: str = ""
    domain: str = ""
    idp_groups: List[str] = field(default_factory=list)
    issued_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 3600)
