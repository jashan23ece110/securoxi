"""
SECUROXI AI Intelligence 2.0 — Secure Multi-Agent Coordination Types & Enums
Defines authority levels, handoff states, conflict types, verification tiers,
and coordination completion statuses.
"""

from enum import Enum


class AuthorityLevel(str, Enum):
    """
    Explicit authority levels for agent outputs and decisions.
    Precedence: AUTHORITATIVE > VERIFIED > SUPPORTED > ADVISORY.
    """
    ADVISORY = "ADVISORY"
    SUPPORTED = "SUPPORTED"
    VERIFIED = "VERIFIED"
    AUTHORITATIVE = "AUTHORITATIVE"


class HandoffStatus(str, Enum):
    """Lifecycle status of a structured inter-agent handoff."""
    REQUESTED = "REQUESTED"
    AUTHORIZED = "AUTHORIZED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class VerificationState(str, Enum):
    """Verification classification of an individual or synthesized multi-agent result."""
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    FAILED = "FAILED"
    CONFLICTING = "CONFLICTING"


class ConflictType(str, Enum):
    """Categorization of inter-agent or authority conflicts."""
    SECURITY_CONFLICT = "SECURITY_CONFLICT"
    EVIDENCE_CONFLICT = "EVIDENCE_CONFLICT"
    SOURCE_CONFLICT = "SOURCE_CONFLICT"
    REQUIREMENT_CONFLICT = "REQUIREMENT_CONFLICT"
    AGENT_RESULT_CONFLICT = "AGENT_RESULT_CONFLICT"
    AUTHORITY_CONFLICT = "AUTHORITY_CONFLICT"
    STATE_CONFLICT = "STATE_CONFLICT"


class CoordinationCompletionStatus(str, Enum):
    """Structured terminal status of a multi-agent coordination workflow."""
    COMPLETED = "COMPLETED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CONFLICTING = "CONFLICTING"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
