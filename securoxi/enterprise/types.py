"""
SECUROXI AI Intelligence 2.0 — Enterprise Organizations & Workspaces Types
"""

from enum import Enum


class OrganizationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    ARCHIVED = "ARCHIVED"


class WorkspaceType(str, Enum):
    GENERAL = "GENERAL"
    HIRING = "HIRING"
    SECURITY = "SECURITY"
    RESEARCH = "RESEARCH"
    OPERATIONS = "OPERATIONS"


class WorkspaceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class MembershipStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INVITED = "INVITED"
    DEACTIVATED = "DEACTIVATED"


class EnterpriseRole(str, Enum):
    ORG_ADMIN = "ORG_ADMIN"
    WORKSPACE_ADMIN = "WORKSPACE_ADMIN"
    MEMBER = "MEMBER"
    GUEST = "GUEST"
