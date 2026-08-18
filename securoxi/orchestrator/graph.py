"""
SECUROXI AI Intelligence 2.0 — Orchestrator Execution DAG & Node Model
Implements graph dependency resolution, topological sort, circular dependency detection,
fan-out/fan-in parallel execution support, and conditional branching.
"""

import time
import uuid
from typing import Dict, Any, List, Set, Optional, Callable
from dataclasses import dataclass, field
from securoxi.orchestrator.types import (
    NodeType,
    NodeState,
    ExecutionType,
    TrustLevel,
)
from securoxi.orchestrator.errors import InvalidStateTransitionError


@dataclass
class ExecutionNode:
    """An individual execution node in the DAG."""
    node_id: str = field(default_factory=lambda: f"NODE-{uuid.uuid4().hex[:8].upper()}")
    run_id: str = ""
    node_type: NodeType = NodeType.TRANSFORM
    name: str = ""
    description: str = ""
    execution_type: ExecutionType = ExecutionType.DETERMINISTIC
    trust_level: TrustLevel = TrustLevel.LOW_RISK
    dependencies: List[str] = field(default_factory=list)  # List of node_ids that must complete first
    timeout_sec: float = 60.0
    max_retries: int = 3
    state: NodeState = NodeState.PENDING
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    idempotency_key: Optional[str] = None
    action_fn: Optional[Callable[..., Any]] = None  # Callable executed when node runs
    condition_fn: Optional[Callable[..., bool]] = None  # Predicate determining whether node should execute or skip
    tool_id: Optional[str] = None  # Target tool if node_type == TOOL
    agent_id: Optional[str] = None  # Target agent if node_type == AGENT
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "run_id": self.run_id,
            "node_type": self.node_type.value,
            "name": self.name,
            "description": self.description,
            "execution_type": self.execution_type.value,
            "trust_level": self.trust_level.value,
            "dependencies": self.dependencies,
            "timeout_sec": self.timeout_sec,
            "max_retries": self.max_retries,
            "state": self.state.value,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error": self.error,
            "retry_count": self.retry_count,
            "idempotency_key": self.idempotency_key,
            "tool_id": self.tool_id,
            "agent_id": self.agent_id,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
        }

    def transition_to(self, new_state: NodeState):
        """Validates and applies state transitions for the node."""
        valid_transitions = {
            NodeState.PENDING: {NodeState.READY, NodeState.RUNNING, NodeState.WAITING_FOR_APPROVAL, NodeState.SKIPPED, NodeState.CANCELLED, NodeState.BLOCKED},
            NodeState.READY: {NodeState.RUNNING, NodeState.WAITING_FOR_APPROVAL, NodeState.SKIPPED, NodeState.CANCELLED},
            NodeState.WAITING_FOR_APPROVAL: {NodeState.READY, NodeState.RUNNING, NodeState.BLOCKED, NodeState.CANCELLED, NodeState.FAILED, NodeState.COMPLETED},
            NodeState.RUNNING: {NodeState.COMPLETED, NodeState.FAILED, NodeState.WAITING, NodeState.CANCELLED, NodeState.READY, NodeState.WAITING_FOR_APPROVAL},
            NodeState.WAITING: {NodeState.RUNNING, NodeState.FAILED, NodeState.CANCELLED},
            NodeState.COMPLETED: set(),
            NodeState.FAILED: {NodeState.READY},  # Can be reset to READY for explicit retry
            NodeState.SKIPPED: set(),
            NodeState.CANCELLED: set(),
            NodeState.BLOCKED: {NodeState.READY, NodeState.CANCELLED, NodeState.FAILED},
        }

        if new_state not in valid_transitions.get(self.state, set()):
            raise InvalidStateTransitionError(
                f"Invalid node state transition from {self.state.value} to {new_state.value} for node {self.node_id}"
            )

        self.state = new_state
        now = time.time()
        if new_state == NodeState.RUNNING and not self.started_at:
            self.started_at = now
        elif new_state in {NodeState.COMPLETED, NodeState.FAILED, NodeState.SKIPPED, NodeState.CANCELLED}:
            self.completed_at = now
            if self.started_at:
                self.duration_ms = (self.completed_at - self.started_at) * 1000.0


class ExecutionDAG:
    """Directed Acyclic Graph representing the execution plan for a run."""

    def __init__(self, run_id: str = ""):
        self.run_id = run_id
        self.nodes: Dict[str, ExecutionNode] = {}
        self.edges: Dict[str, List[str]] = {}  # parent_id -> list of child_ids

    def add_node(self, node: ExecutionNode) -> str:
        """Adds a node to the DAG."""
        if not node.run_id and self.run_id:
            node.run_id = self.run_id
        self.nodes[node.node_id] = node
        if node.node_id not in self.edges:
            self.edges[node.node_id] = []

        # Register reverse edges from dependencies
        for dep_id in node.dependencies:
            if dep_id not in self.edges:
                self.edges[dep_id] = []
            if node.node_id not in self.edges[dep_id]:
                self.edges[dep_id].append(node.node_id)

        self._validate_no_cycles()
        return node.node_id

    def get_node(self, node_id: str) -> Optional[ExecutionNode]:
        return self.nodes.get(node_id)

    def get_children(self, node_id: str) -> List[ExecutionNode]:
        """Returns immediate downstream dependent nodes."""
        child_ids = self.edges.get(node_id, [])
        return [self.nodes[cid] for cid in child_ids if cid in self.nodes]

    def get_parents(self, node_id: str) -> List[ExecutionNode]:
        """Returns upstream dependency nodes."""
        node = self.nodes.get(node_id)
        if not node:
            return []
        return [self.nodes[pid] for pid in node.dependencies if pid in self.nodes]

    def get_ready_nodes(self) -> List[ExecutionNode]:
        """
        Returns nodes that are ready to execute:
        1. Node is in PENDING state.
        2. All upstream dependencies are COMPLETED (or SKIPPED).
        """
        ready = []
        for node_id, node in self.nodes.items():
            if node.state != NodeState.PENDING:
                continue

            # Check upstream dependencies
            all_deps_satisfied = True
            for dep_id in node.dependencies:
                dep_node = self.nodes.get(dep_id)
                if not dep_node or dep_node.state not in {NodeState.COMPLETED, NodeState.SKIPPED}:
                    all_deps_satisfied = False
                    break

            if all_deps_satisfied:
                ready.append(node)

        return ready

    def topological_sort(self) -> List[ExecutionNode]:
        """Returns nodes in topological dependency order."""
        in_degree: Dict[str, int] = {nid: len(node.dependencies) for nid, node in self.nodes.items()}
        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        sorted_nodes: List[ExecutionNode] = []

        while queue:
            curr_id = queue.pop(0)
            sorted_nodes.append(self.nodes[curr_id])

            for child_id in self.edges.get(curr_id, []):
                in_degree[child_id] -= 1
                if in_degree[child_id] == 0:
                    queue.append(child_id)

        if len(sorted_nodes) != len(self.nodes):
            raise InvalidStateTransitionError("Cyclic dependency detected in Execution DAG.")

        return sorted_nodes

    def _validate_no_cycles(self):
        """Ensures the graph remains strictly acyclic."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for neighbor_id in self.edges.get(node_id, []):
                if neighbor_id not in visited:
                    if has_cycle(neighbor_id):
                        return True
                elif neighbor_id in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if has_cycle(node_id):
                    raise InvalidStateTransitionError(f"Cycle detected in execution graph involving node {node_id}")

    def propagate_skip(self, failed_or_skipped_node_id: str):
        """Recursively marks unexecutable downstream children as SKIPPED or BLOCKED."""
        to_process = list(self.edges.get(failed_or_skipped_node_id, []))
        while to_process:
            child_id = to_process.pop(0)
            child_node = self.nodes.get(child_id)
            if child_node and child_node.state in {NodeState.PENDING, NodeState.READY}:
                child_node.transition_to(NodeState.SKIPPED)
                to_process.extend(self.edges.get(child_id, []))

    def is_complete(self) -> bool:
        """Returns True if all nodes have reached a terminal state."""
        terminal_states = {NodeState.COMPLETED, NodeState.FAILED, NodeState.SKIPPED, NodeState.CANCELLED}
        return all(node.state in terminal_states for node in self.nodes.values())

    def has_failures(self) -> bool:
        """Returns True if any node has failed."""
        return any(node.state == NodeState.FAILED for node in self.nodes.values())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "node_count": len(self.nodes),
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "edges": self.edges,
            "is_complete": self.is_complete(),
            "has_failures": self.has_failures(),
        }
