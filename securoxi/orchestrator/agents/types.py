"""
SECUROXI AI Intelligence 2.0 — Agent Runtime Types & Enums
Defines agent domains, capabilities, lifecycle states, risk levels, action types,
and memory access permissions.
"""

from enum import Enum


class AgentDomain(str, Enum):
    """Functional domain classification for specialized agents."""
    SECURITY = "SECURITY"
    HIRING = "HIRING"
    RETRIEVAL = "RETRIEVAL"
    FORENSICS = "FORENSICS"
    INCIDENTS = "INCIDENTS"
    RESEARCH = "RESEARCH"
    GENERAL = "GENERAL"


class AgentCapability(str, Enum):
    """Machine-readable capability taxonomy advertised by agents."""
    SECURITY_ANALYSIS = "SECURITY_ANALYSIS"
    DOCUMENT_RETRIEVAL = "DOCUMENT_RETRIEVAL"
    CANDIDATE_SCREENING = "CANDIDATE_SCREENING"
    JD_MATCHING = "JD_MATCHING"
    FORENSIC_ANALYSIS = "FORENSIC_ANALYSIS"
    INCIDENT_INVESTIGATION = "INCIDENT_INVESTIGATION"
    REPORT_GENERATION = "REPORT_GENERATION"
    GENERAL_REASONING = "GENERAL_REASONING"


class AgentRiskLevel(str, Enum):
    """Operational risk rating of an agent's intended capabilities."""
    LOW = "LOW"            # Read-only or analysis operations
    MEDIUM = "MEDIUM"      # Non-destructive ranking or transformation
    HIGH = "HIGH"          # Quarantine, tagging, or candidate rejection
    CRITICAL = "CRITICAL"  # Policy modifications, mass deletion, external side-effects


class AgentLifecycleState(str, Enum):
    """Strict lifecycle state machine for agent execution."""
    REGISTERED = "REGISTERED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    DEGRADED = "DEGRADED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AgentActionType(str, Enum):
    """Standardized decision actions an agent can propose to the orchestrator."""
    CONTINUE = "CONTINUE"
    USE_TOOL = "USE_TOOL"
    ASK_CLARIFICATION = "ASK_CLARIFICATION"
    REQUEST_APPROVAL = "REQUEST_APPROVAL"
    HANDOFF = "HANDOFF"
    ESCALATE = "ESCALATE"
    REPLAN = "REPLAN"
    FINISH = "FINISH"
    ABORT = "ABORT"


class MemoryAccessPermission(str, Enum):
    """Granular permissions for interacting with orchestrator memory scopes."""
    READ_WORKING = "READ_WORKING"
    WRITE_WORKING = "WRITE_WORKING"
    READ_TASK = "READ_TASK"
    WRITE_TASK = "WRITE_TASK"
    READ_PERSISTENT = "READ_PERSISTENT"
    WRITE_PERSISTENT = "WRITE_PERSISTENT"
