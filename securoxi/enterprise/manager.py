"""
SECUROXI AI Intelligence 2.0 — Enterprise Organization & Workspace Manager
Coordinates organization lifecycles, workspace hierarchies, memberships, and secure context propagation.
"""

from typing import Dict, Any, List, Optional
import time
from securoxi.enterprise.types import (
    OrganizationStatus,
    WorkspaceType,
    WorkspaceStatus,
    MembershipStatus,
    EnterpriseRole,
)
from securoxi.enterprise.models import (
    Organization,
    Workspace,
    Team,
    Membership,
    OrganizationContext,
    OrganizationSettings,
    WorkspaceSettings,
)
from securoxi.logger import get_logger

logger = get_logger("enterprise.manager")


class EnterpriseOrganizationManager:
    """
    Enterprise Organization & Workspace Manager.
    Enforces multi-organization isolation, workspace boundaries, and membership authorization.
    """

    def __init__(self):
        self._organizations: Dict[str, Organization] = {}
        self._workspaces: Dict[str, Workspace] = {}
        self._memberships: Dict[str, Membership] = {}
        self._teams: Dict[str, Team] = {}

    def create_organization(
        self,
        name: str,
        slug: str,
        creator_user_id: Optional[str] = None,
        settings: Optional[OrganizationSettings] = None,
    ) -> Organization:
        """Creates a new organization and provisions its default General workspace."""
        org = Organization(
            name=name,
            slug=slug,
            settings=settings or OrganizationSettings(),
        )
        self._organizations[org.organization_id] = org

        # Create Default Workspace
        default_ws = Workspace(
            organization_id=org.organization_id,
            name=f"{name} General",
            workspace_type=WorkspaceType.GENERAL,
        )
        self._workspaces[default_ws.workspace_id] = default_ws

        # Add Creator as ORG_ADMIN if provided
        if creator_user_id:
            membership = Membership(
                organization_id=org.organization_id,
                user_id=creator_user_id,
                role=EnterpriseRole.ORG_ADMIN,
                status=MembershipStatus.ACTIVE,
                allowed_workspaces=[default_ws.workspace_id],
            )
            self._memberships[membership.membership_id] = membership

        logger.info(f"Created Organization '{org.name}' ({org.organization_id}) with default workspace '{default_ws.workspace_id}'")
        return org

    def create_workspace(
        self,
        organization_id: str,
        name: str,
        workspace_type: WorkspaceType = WorkspaceType.GENERAL,
        settings: Optional[WorkspaceSettings] = None,
    ) -> Optional[Workspace]:
        """Creates a specialized functional workspace inside an active organization."""
        if organization_id not in self._organizations:
            logger.error(f"Cannot create workspace: Organization '{organization_id}' not found")
            return None

        org = self._organizations[organization_id]
        if org.status != OrganizationStatus.ACTIVE:
            logger.error(f"Cannot create workspace: Organization '{organization_id}' is not ACTIVE ({org.status.value})")
            return None

        ws = Workspace(
            organization_id=organization_id,
            name=name,
            workspace_type=workspace_type,
            settings=settings or WorkspaceSettings(display_name=name),
        )
        self._workspaces[ws.workspace_id] = ws
        logger.info(f"Created Workspace '{ws.name}' ({ws.workspace_id}) under Organization '{organization_id}'")
        return ws

    def invite_member(
        self,
        organization_id: str,
        user_id: str,
        role: EnterpriseRole = EnterpriseRole.MEMBER,
        allowed_workspaces: Optional[List[str]] = None,
    ) -> Optional[Membership]:
        """Invites a user to join an organization with specified workspace access."""
        if organization_id not in self._organizations:
            return None

        # Verify allowed workspaces belong to this organization
        org_workspaces = [w.workspace_id for w in self._workspaces.values() if w.organization_id == organization_id]
        valid_ws = [ws for ws in (allowed_workspaces or org_workspaces) if ws in org_workspaces]

        membership = Membership(
            organization_id=organization_id,
            user_id=user_id,
            role=role,
            status=MembershipStatus.ACTIVE,
            allowed_workspaces=valid_ws,
        )
        self._memberships[membership.membership_id] = membership
        logger.info(f"Added member '{user_id}' to Organization '{organization_id}' with role '{role.value}'")
        return membership

    def resolve_context(
        self,
        user_id: str,
        target_organization_id: str,
        target_workspace_id: Optional[str] = None,
    ) -> Optional[OrganizationContext]:
        """
        Validates user membership and resolves an authenticated, immutable OrganizationContext.
        Rejects cross-organization access attempts.
        """
        # Find active membership
        membership = next(
            (m for m in self._memberships.values()
             if m.user_id == user_id and m.organization_id == target_organization_id and m.status == MembershipStatus.ACTIVE),
            None
        )
        if not membership:
            logger.warning(f"Access Denied: User '{user_id}' has no active membership in Organization '{target_organization_id}'")
            return None

        org = self._organizations.get(target_organization_id)
        if not org or org.status != OrganizationStatus.ACTIVE:
            logger.warning(f"Access Denied: Organization '{target_organization_id}' is suspended or archived")
            return None

        # Resolve target workspace
        if target_workspace_id:
            ws = self._workspaces.get(target_workspace_id)
            if not ws or ws.organization_id != target_organization_id or ws.status != WorkspaceStatus.ACTIVE:
                logger.warning(f"Access Denied: Workspace '{target_workspace_id}' not found or inactive in Organization '{target_organization_id}'")
                return None
            if membership.role != EnterpriseRole.ORG_ADMIN and target_workspace_id not in membership.allowed_workspaces:
                logger.warning(f"Access Denied: User '{user_id}' not authorized for Workspace '{target_workspace_id}'")
                return None
            selected_ws_id = target_workspace_id
        else:
            selected_ws_id = membership.allowed_workspaces[0] if membership.allowed_workspaces else next(
                (w.workspace_id for w in self._workspaces.values() if w.organization_id == target_organization_id),
                "WS-DEFAULT"
            )

        return OrganizationContext(
            organization_id=target_organization_id,
            workspace_id=selected_ws_id,
            actor_id=user_id,
            role=membership.role,
        )

    def validate_resource_access(
        self,
        context: OrganizationContext,
        resource_org_id: str,
        resource_workspace_id: Optional[str] = None,
    ) -> bool:
        """
        Enforces that a request's OrganizationContext matches resource ownership.
        Strictly blocks cross-organization and unauthorized cross-workspace access.
        """
        if context.organization_id != resource_org_id:
            logger.warning(f"Cross-Organization Access Blocked: Context Org '{context.organization_id}' != Resource Org '{resource_org_id}'")
            return False

        if resource_workspace_id and context.role != EnterpriseRole.ORG_ADMIN:
            if context.workspace_id != resource_workspace_id:
                logger.warning(f"Cross-Workspace Access Blocked: Context WS '{context.workspace_id}' != Resource WS '{resource_workspace_id}'")
                return False

        return True
