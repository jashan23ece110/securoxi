"""
SECUROXI AI Intelligence 2.0 — Persistence & Memory Types
Defines memory scopes, memory item types, memory sources, checkpoint triggers,
and worker lease states.
"""

from enum import Enum


class MemoryScope(str, Enum):
    """Lifecycle boundary of stored memory."""
    WORKING = "WORKING"          # Transient to the current active execution run
    TASK = "TASK"                # Preserved across runs/checkpoints for the current task
    PERSISTENT = "PERSISTENT"    # Durable across multiple tasks within tenant


class MemoryType(str, Enum):
    """Categorization of facts and evidence stored in memory."""
    FACT = "FACT"
    EVIDENCE = "EVIDENCE"
    INTERMEDIATE_RESULT = "INTERMEDIATE_RESULT"
    PLAN_STATE = "PLAN_STATE"
    USER_CONSTRAINT = "USER_CONSTRAINT"
    SYSTEM_STATE = "SYSTEM_STATE"
    TOOL_RESULT = "TOOL_RESULT"
    DERIVED_RESULT = "DERIVED_RESULT"


class MemorySource(str, Enum):
    """Provenance origin of stored memory."""
    DETERMINISTIC_ENGINE = "DETERMINISTIC_ENGINE"  # Highest authority
    VERIFIED_TOOL = "VERIFIED_TOOL"                # Second authority
    USER = "USER"                                  # Third authority (current constraints)
    TRUSTED_DOCUMENT = "TRUSTED_DOCUMENT"          # Fourth authority
    DERIVED = "DERIVED"                            # Fifth authority
    LLM_ADVISORY = "LLM_ADVISORY"                  # Sixth authority (Advisory only)


class MemoryTrustHierarchy(int, Enum):
    """Deterministic authority precedence for resolving conflicting memory items."""
    DETERMINISTIC_SECURITY = 1  # Security engine / Policy Invariant (Wins all conflicts)
    VERIFIED_TOOL = 2           # Tool result validated against schema
    USER_CONSTRAINT = 3         # Explicit current user constraints
    TRUSTED_EVIDENCE = 4        # Extracted native text from verified document
    DERIVED_REASONING = 5       # Intermediate calculated score/aggregation
    LLM_ADVISORY = 6            # Advisory model output (Lowest)


class CheckpointTrigger(str, Enum):
    """Event that triggered creation of an execution checkpoint."""
    NODE_COMPLETED = "NODE_COMPLETED"
    BEFORE_LONG_RUNNING_OP = "BEFORE_LONG_RUNNING_OP"
    BEFORE_HUMAN_APPROVAL = "BEFORE_HUMAN_APPROVAL"
    BEFORE_REPLANNING = "BEFORE_REPLANNING"
    PERIODIC_HEARTBEAT = "PERIODIC_HEARTBEAT"
    RUN_PAUSED = "RUN_PAUSED"
    RUN_CANCELLED = "RUN_CANCELLED"


class LeaseStatus(str, Enum):
    """State of an execution worker lease on a node."""
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    RELEASED = "RELEASED"
    REVOKED = "REVOKED"
