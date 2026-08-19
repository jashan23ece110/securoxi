"""
SECUROXI AI Intelligence 2.0 — Enterprise Digital Twin Graph Engine (Phase 8 Stage 51)
Maintains queryable adjacency representations of enterprise entities, relationships, and dependencies.
Strictly maintains the invariant that the Graph is a Contextual Model, NOT an Authorization or Security Authority.
"""

from typing import Dict, Any, List, Optional, Set
import time
from securoxi.enterprise.graph.types import (
    NodeType,
    EdgeType,
    GraphTrustLevel,
)
from securoxi.enterprise.graph.models import (
    GraphNode,
    GraphEdge,
    ImpactAnalysisResult,
)
from securoxi.logger import get_logger

logger = get_logger("enterprise.graph.engine")


class EnterpriseDigitalTwinGraph:
    """
    Enterprise Digital Twin & Organization Intelligence Graph.
    Maintains entity nodes, provenance-preserving edges, and executes bounded impact analyses.
    """

    def __init__(self):
        self._nodes: Dict[str, GraphNode] = {}  # node_id -> GraphNode
        self._edges: Dict[str, GraphEdge] = {}  # edge_id -> GraphEdge
        self._adj: Dict[str, List[str]] = {}    # node_id -> List[edge_id]

    def add_node(
        self,
        organization_id: str,
        workspace_id: str,
        node_type: NodeType,
        name: str,
        properties: Optional[Dict[str, Any]] = None,
        source_reference: str = "",
    ) -> GraphNode:
        """Adds or updates an entity node in the intelligence graph."""
        node = GraphNode(
            organization_id=organization_id,
            workspace_id=workspace_id,
            node_type=node_type,
            name=name,
            properties=properties or {},
            source_reference=source_reference,
        )
        self._nodes[node.node_id] = node
        self._adj[node.node_id] = []
        logger.info(f"Registered Graph Node '{node.node_id}' ({node_type.value}: '{name}') for Org '{organization_id}'")
        return node

    def add_edge(
        self,
        organization_id: str,
        source_node_id: str,
        target_node_id: str,
        edge_type: EdgeType = EdgeType.DEPENDS_ON,
        trust_level: GraphTrustLevel = GraphTrustLevel.VERIFIED,
        confidence: float = 1.0,
        provenance: str = "",
    ) -> Optional[GraphEdge]:
        """
        Creates a directed edge between two existing nodes.
        Strictly enforces tenant isolation: both nodes must belong to the organization.
        """
        src = self._nodes.get(source_node_id)
        tgt = self._nodes.get(target_node_id)

        if not src or not tgt:
            logger.error(f"Cannot create edge: Node not found (src={source_node_id}, tgt={target_node_id})")
            return None

        if src.organization_id != organization_id or tgt.organization_id != organization_id:
            logger.error(f"Cross-tenant edge rejected: Org '{organization_id}' tried connecting across tenants")
            return None

        edge = GraphEdge(
            organization_id=organization_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            edge_type=edge_type,
            trust_level=trust_level,
            confidence=confidence,
            provenance=provenance,
        )
        self._edges[edge.edge_id] = edge
        self._adj[source_node_id].append(edge.edge_id)
        logger.info(f"Created Graph Edge '{edge.edge_id}' ({edge_type.value}: {source_node_id} -> {target_node_id})")
        return edge

    def get_impact_radius(self, node_id: str, max_depth: int = 2) -> ImpactAnalysisResult:
        """
        Computes bounded impact radius (BFS traversal) of dependent entities.
        Does not allow infinite traversal loops.
        """
        target = self._nodes.get(node_id)
        if not target or not target.is_active:
            return ImpactAnalysisResult(target_node_id=node_id, organization_id="UNKNOWN")

        visited: Set[str] = {node_id}
        queue: List[tuple[str, int]] = [(node_id, 0)]
        affected: List[GraphNode] = []

        while queue:
            curr_id, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            for edge_id in self._adj.get(curr_id, []):
                edge = self._edges.get(edge_id)
                if not edge or not edge.is_active:
                    continue
                neighbor_id = edge.target_node_id
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    neighbor_node = self._nodes.get(neighbor_id)
                    if neighbor_node and neighbor_node.is_active:
                        affected.append(neighbor_node)
                        queue.append((neighbor_id, depth + 1))

        return ImpactAnalysisResult(
            target_node_id=node_id,
            organization_id=target.organization_id,
            affected_nodes=affected,
            impact_depth=max_depth,
        )

    def delete_node(self, node_id: str) -> bool:
        """
        Deletion propagation: Immediately deactivates node and invalidates all incident edges.
        """
        if node_id not in self._nodes:
            return False

        node = self._nodes[node_id]
        node.is_active = False

        # Invalidate outgoing edges
        for edge_id in self._adj.get(node_id, []):
            if edge_id in self._edges:
                self._edges[edge_id].is_active = False

        # Invalidate incoming edges
        for edge in self._edges.values():
            if edge.target_node_id == node_id:
                edge.is_active = False

        logger.info(f"Propagated Deletion: Inactivated Graph Node '{node_id}' and adjacent edges")
        return True

    def get_nodes(self, organization_id: str, workspace_id: Optional[str] = None) -> List[GraphNode]:
        """Returns active graph nodes strictly scoped by tenant."""
        results = [n for n in self._nodes.values() if n.organization_id == organization_id and n.is_active]
        if workspace_id:
            results = [n for n in results if n.workspace_id == workspace_id]
        return results
