"""
SECUROXI AI Intelligence 2.0 — Advanced Enterprise RBAC, Identity & SSO Enums & Types
"""

from enum import Enum


class Permission(str, Enum):
    # Organization
    ORG_READ = "organization.read"
    ORG_UPDATE = "organization.update"
    MEMBER_READ = "member.read"
    MEMBER_INVITE = "member.invite"
    MEMBER_REMOVE = "member.remove"
    SSO_MANAGE = "sso.manage"

    # Workspace
    WS_READ = "workspace.read"
    WS_UPDATE = "workspace.update"
    WS_MANAGE = "workspace.manage"

    # Hiring / ATS
    CANDIDATE_READ = "candidate.read"
    CANDIDATE_SCREEN = "candidate.screen"
    CANDIDATE_EXPORT = "candidate.export"
    ATS_READ = "ats.read"
    ATS_WRITE = "ats.write"

    # Security & Forensics
    INVESTIGATION_READ = "investigation.read"
    INVESTIGATION_CREATE = "investigation.create"
    INCIDENT_READ = "incident.read"
    INCIDENT_UPDATE = "incident.update"
    EVIDENCE_READ = "evidence.read"
    SECURITY_ACTION = "security.action"

    # Governance & Approval
    APPROVAL_READ = "approval.read"
    APPROVAL_APPROVE = "approval.approve"
    APPROVAL_REJECT = "approval.reject"

    # Audit & Policy
    AUDIT_READ = "audit.read"
    POLICY_MANAGE = "policy.manage"


class SSOProtocol(str, Enum):
    OIDC = "OIDC"
    SAML_2_0 = "SAML_2_0"
    OAUTH2 = "OAUTH2"


class AuthMethod(str, Enum):
    LOCAL_PASSWORD = "LOCAL_PASSWORD"
    ENTERPRISE_SSO = "ENTERPRISE_SSO"
    SERVICE_KEY = "SERVICE_KEY"
    DELEGATED_AGENT = "DELEGATED_AGENT"


class DelegationScope(str, Enum):
    TASK_BOUNDED = "TASK_BOUNDED"
    READ_ONLY = "READ_ONLY"
    FULL_DELEGATION = "FULL_DELEGATION"
