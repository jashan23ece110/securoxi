"""
SECUROXI AI Intelligence 2.0 — Enterprise Digital Twin Models (Phase 8 Stage 51)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
import time
import uuid
from securoxi.enterprise.graph.types import (
    NodeType,
    EdgeType,
    GraphTrustLevel,
)


@dataclass
class GraphNode:
    """Canonical representation of an entity node in the intelligence graph."""
    node_id: str = field(default_factory=lambda: f"NODE-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-DEFAULT"
    node_type: NodeType = NodeType.DOCUMENT
    name: str = "Enterprise Entity"
    properties: Dict[str, Any] = field(default_factory=dict)
    source_reference: str = ""
    is_active: bool = True
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class GraphEdge:
    """Provenance-preserving edge connecting two nodes."""
    edge_id: str = field(default_factory=lambda: f"EDGE-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    source_node_id: str = "NODE-SRC"
    target_node_id: str = "NODE-TGT"
    edge_type: EdgeType = EdgeType.DEPENDS_ON
    trust_level: GraphTrustLevel = GraphTrustLevel.VERIFIED
    confidence: float = 1.0
    provenance: str = ""
    is_active: bool = True
    created_at: float = field(default_factory=time.time)


@dataclass
class ImpactAnalysisResult:
    """Bounded impact radius result for a target node."""
    target_node_id: str
    organization_id: str
    affected_nodes: List[GraphNode] = field(default_factory=list)
    impact_depth: int = 1
    analyzed_at: float = field(default_factory=time.time)
