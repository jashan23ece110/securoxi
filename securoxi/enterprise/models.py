"""
SECUROXI AI Intelligence 2.0 — Enterprise Organizations & Workspace Models
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time
import uuid
from securoxi.enterprise.types import (
    OrganizationStatus,
    WorkspaceType,
    WorkspaceStatus,
    MembershipStatus,
    EnterpriseRole,
)


@dataclass
class OrganizationSettings:
    """Enterprise organization-wide configuration and policies."""
    default_workspace_type: WorkspaceType = WorkspaceType.GENERAL
    allowed_domains: List[str] = field(default_factory=list)
    enforce_strict_isolation: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkspaceSettings:
    """Workspace-level configuration and functional capabilities."""
    display_name: str = ""
    enabled_capabilities: List[str] = field(default_factory=lambda: ["COMMAND", "RAG", "SECURITY", "HIRING"])
    description: str = ""


@dataclass
class Organization:
    """First-class enterprise Organization entity."""
    organization_id: str = field(default_factory=lambda: f"ORG-{uuid.uuid4().hex[:8].upper()}")
    name: str = "Default Enterprise"
    slug: str = "default-enterprise"
    status: OrganizationStatus = OrganizationStatus.ACTIVE
    settings: OrganizationSettings = field(default_factory=OrganizationSettings)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "organization_id": self.organization_id,
            "name": self.name,
            "slug": self.slug,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Workspace:
    """Functional workspace within an Organization."""
    workspace_id: str = field(default_factory=lambda: f"WS-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    name: str = "General Workspace"
    workspace_type: WorkspaceType = WorkspaceType.GENERAL
    status: WorkspaceStatus = WorkspaceStatus.ACTIVE
    settings: WorkspaceSettings = field(default_factory=WorkspaceSettings)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "organization_id": self.organization_id,
            "name": self.name,
            "workspace_type": self.workspace_type.value,
            "status": self.status.value,
            "created_at": self.created_at,
        }


@dataclass
class Team:
    """Organizational team within an Organization and optional Workspace."""
    team_id: str = field(default_factory=lambda: f"TEAM-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: Optional[str] = None
    name: str = "Core Team"
    members: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class Membership:
    """User membership within an Organization."""
    membership_id: str = field(default_factory=lambda: f"MEM-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    user_id: str = "USER-DEFAULT"
    role: EnterpriseRole = EnterpriseRole.MEMBER
    status: MembershipStatus = MembershipStatus.ACTIVE
    allowed_workspaces: List[str] = field(default_factory=list)
    joined_at: float = field(default_factory=time.time)


@dataclass
class OrganizationContext:
    """
    Canonical, immutable organizational context propagated through all API calls,
    orchestrator tasks, agents, retrieval queries, and governance requests.
    """
    organization_id: str
    workspace_id: str
    actor_id: str
    role: EnterpriseRole = EnterpriseRole.MEMBER
    tenant_compatibility_id: Optional[str] = None

    @property
    def tenant_id(self) -> str:
        """Compatibility bridge: resolves to organization_id or legacy tenant_id."""
        return self.tenant_compatibility_id or self.organization_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "actor_id": self.actor_id,
            "role": self.role.value,
            "tenant_id": self.tenant_id,
        }
