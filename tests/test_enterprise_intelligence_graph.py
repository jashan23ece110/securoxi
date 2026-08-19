"""
SECUROXI AI Intelligence 2.0 — Enterprise Digital Twin Test Suite (Phase 8 Stage 51)
Validates entity resolution, provenance-preserving edges, bounded impact radius analysis,
deletion propagation, and strict multi-tenant boundary checks.
"""

import pytest
from securoxi.enterprise.graph import (
    EnterpriseDigitalTwinGraph,
    NodeType,
    EdgeType,
    GraphTrustLevel,
)


# =========================================================================
# 1. GRAPH NODE & EDGE REGISTRATION WITH PROVENANCE
# =========================================================================

def test_node_and_edge_registration_with_provenance():
    """Verifies registering entity nodes and connecting them with typed, provenance-backed edges."""
    graph = EnterpriseDigitalTwinGraph()

    # 1. Register Nodes
    policy_node = graph.add_node(
        organization_id="ORG-TEST",
        workspace_id="WS-MAIN",
        node_type=NodeType.POLICY,
        name="Data Retention Standard v2",
        source_reference="SRC-POL-909",
    )
    workflow_node = graph.add_node(
        organization_id="ORG-TEST",
        workspace_id="WS-MAIN",
        node_type=NodeType.TASK,
        name="Nightly ATS Sync Workflow",
        source_reference="TASK-SYNC-101",
    )

    # 2. Add Edge
    edge = graph.add_edge(
        organization_id="ORG-TEST",
        source_node_id=policy_node.node_id,
        target_node_id=workflow_node.node_id,
        edge_type=EdgeType.APPLIES_TO,
        trust_level=GraphTrustLevel.AUTHORITATIVE,
        provenance="GOV-AUDIT-404",
    )
    assert edge is not None
    assert edge.trust_level == GraphTrustLevel.AUTHORITATIVE
    assert edge.edge_type == EdgeType.APPLIES_TO


# =========================================================================
# 2. BOUNDED IMPACT RADIUS ANALYSIS
# =========================================================================

def test_bounded_impact_radius_analysis():
    """Verifies that impact analysis identifies dependent nodes across bounded hops without infinite loops."""
    graph = EnterpriseDigitalTwinGraph()

    n1 = graph.add_node("ORG-TEST", "WS-MAIN", NodeType.POLICY, "Core Security Policy")
    n2 = graph.add_node("ORG-TEST", "WS-MAIN", NodeType.INTEGRATION, "Greenhouse ATS Connector")
    n3 = graph.add_node("ORG-TEST", "WS-MAIN", NodeType.JOB, "Senior Security Architect Job")

    # Connect: Policy -> Integration -> Job
    graph.add_edge("ORG-TEST", n1.node_id, n2.node_id, EdgeType.APPLIES_TO)
    graph.add_edge("ORG-TEST", n2.node_id, n3.node_id, EdgeType.AFFECTS)

    # Compute Impact Radius of Policy (Depth 2)
    impact = graph.get_impact_radius(n1.node_id, max_depth=2)
    assert len(impact.affected_nodes) == 2
    affected_ids = [n.node_id for n in impact.affected_nodes]
    assert n2.node_id in affected_ids
    assert n3.node_id in affected_ids


# =========================================================================
# 3. DELETION PROPAGATION & TENANT ISOLATION
# =========================================================================

def test_deletion_propagation_and_tenant_isolation():
    """Verifies deletion propagation deactivates adjacent edges, and cross-tenant edges are strictly rejected."""
    graph = EnterpriseDigitalTwinGraph()

    alpha_node = graph.add_node("ORG-ALPHA", "WS-A", NodeType.CANDIDATE, "Candidate Alice")
    alpha_job = graph.add_node("ORG-ALPHA", "WS-A", NodeType.JOB, "Staff Engineer")
    edge = graph.add_edge("ORG-ALPHA", alpha_node.node_id, alpha_job.node_id, EdgeType.CANDIDATE_FOR)
    assert edge is not None

    # Delete Candidate -> Inactivates candidate and connected edge
    graph.delete_node(alpha_node.node_id)
    assert alpha_node.is_active is False
    assert edge.is_active is False

    # Cross-Tenant Edge Attempt (Org Alpha Node -> Org Beta Node) -> Strictly Rejected
    beta_node = graph.add_node("ORG-BETA", "WS-B", NodeType.JOB, "Beta Corp Job")
    cross_edge = graph.add_edge("ORG-ALPHA", alpha_job.node_id, beta_node.node_id, EdgeType.AFFECTS)
    assert cross_edge is None  # Cross-tenant rejected
