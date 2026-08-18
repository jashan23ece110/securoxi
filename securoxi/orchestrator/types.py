"""
SECUROXI AI Intelligence 2.0 — Orchestrator Types & Enums
Defines core enums for trust levels, execution types, node types, run states, and priorities.
"""

from enum import Enum


class TrustLevel(str, Enum):
    """Execution trust levels for nodes, tools, and actors."""
    UNTRUSTED = "UNTRUSTED"        # Untrusted inputs, external unverified payloads
    LOW_RISK = "LOW_RISK"          # Read-only, side-effect free operations
    CONTROLLED = "CONTROLLED"      # Scoped modifications, candidate scoring, bounded search
    HIGH_IMPACT = "HIGH_IMPACT"    # Policy changes, quarantine/block actions, data deletion, privileged access


class ExecutionType(str, Enum):
    """Explicit boundary between deterministic logic and probabilistic model reasoning."""
    DETERMINISTIC = "DETERMINISTIC"  # Rule-based parsers, cryptographic hashes, deterministic policy rules
    AGENTIC = "AGENTIC"              # LLM reasoning, probabilistic qualification, natural language synthesis


class TaskPriority(str, Enum):
    """Priority levels for task scheduling and concurrency allocation."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TaskStatus(str, Enum):
    """High-level lifecycle status for a user task."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"


class RunState(str, Enum):
    """Explicit state machine states for an orchestration execution run."""
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    PAUSING = "PAUSING"
    PAUSED = "PAUSED"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"


class NodeState(str, Enum):
    """Explicit state machine states for individual DAG execution nodes."""
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


class NodeType(str, Enum):
    """Generic types of execution nodes supported by the orchestrator DAG."""
    THINK_PLAN = "THINK_PLAN"            # Agent planning, adaptive decomposition
    TOOL = "TOOL"                        # Explicit tool invocation via ToolRegistry
    RETRIEVAL = "RETRIEVAL"              # Vector search, document retrieval
    AGENT = "AGENT"                      # Pluggable sub-agent execution
    VALIDATION = "VALIDATION"            # Output schema validation, safety gate
    TRANSFORM = "TRANSFORM"              # Data shaping, normalization
    DECISION = "DECISION"                # Conditional branching predicate
    HUMAN_APPROVAL = "HUMAN_APPROVAL"    # Blocking gate for human reviewer sign-off
    FINALIZE = "FINALIZE"                # Result aggregation and final synthesis


class SecurityClassification(str, Enum):
    """Data security classification determining logging and exposure boundaries."""
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class ApprovalStatus(str, Enum):
    """Status for human-in-the-loop approval gates."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
