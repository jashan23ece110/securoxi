"""
SECUROXI AI Intelligence 2.0 — Enterprise Workflow Composer Test Suite (Phase 9 Stage 55)
Validates declarative workflow creation, cycle detection, side-effect-free simulation,
security clearance gates, approval node governance, multi-tenant isolation, and global pause controls.
"""

import pytest
from securoxi.enterprise.workflow import (
    EnterpriseWorkflowComposer,
    WorkflowNode,
    WorkflowEdge,
    NodeType,
    TriggerType,
    WorkflowStatus,
    RunStatus,
)


# =========================================================================
# 1. DECLARATIVE WORKFLOW CREATION & CYCLE DETECTION
# =========================================================================

def test_workflow_creation_and_cycle_validation():
    """Verifies that DAG cycles are rejected and valid workflows pass validation."""
    composer = EnterpriseWorkflowComposer()

    # 1. Create Valid Workflow
    nodes = [
        WorkflowNode(node_id="N-TRIG", node_type=NodeType.TRIGGER, capability_name="EventTrigger"),
        WorkflowNode(node_id="N-SEC", node_type=NodeType.SECURITY_SCAN, capability_name="SecurityAgent"),
        WorkflowNode(node_id="N-SCREEN", node_type=NodeType.HIRING_SCREEN, capability_name="HiringAgent"),
    ]
    edges = [
        WorkflowEdge(source_node_id="N-TRIG", target_node_id="N-SEC"),
        WorkflowEdge(source_node_id="N-SEC", target_node_id="N-SCREEN"),
    ]
    wf = composer.create_workflow(
        organization_id="ORG-TEST",
        workspace_id="WS-CORP",
        name="Candidate Screening Workflow",
        trigger_type=TriggerType.EVENT,
        nodes=nodes,
        edges=edges,
    )
    val = composer.validate_workflow(wf.workflow_id)
    assert val["valid"] is True
    assert val["node_count"] == 3

    # 2. Add Cyclic Edge (N-SCREEN -> N-TRIG) -> Validation must fail
    wf.edges.append(WorkflowEdge(source_node_id="N-SCREEN", target_node_id="N-TRIG"))
    val_cycle = composer.validate_workflow(wf.workflow_id)
    assert val_cycle["valid"] is False
    assert "cycle" in val_cycle["error"].lower()


# =========================================================================
# 2. SIDE-EFFECT-FREE WORKFLOW SIMULATION
# =========================================================================

def test_workflow_simulation():
    """Verifies simulation walks DAG and proposes actions with zero live side-effects."""
    composer = EnterpriseWorkflowComposer()

    nodes = [
        WorkflowNode(node_id="N-TRIG", node_type=NodeType.TRIGGER, capability_name="EventTrigger"),
        WorkflowNode(node_id="N-SEC", node_type=NodeType.SECURITY_SCAN, capability_name="SecurityAgent"),
        WorkflowNode(node_id="N-ACT", node_type=NodeType.ACTION, capability_name="ATS_WRITE", is_high_impact=True),
    ]
    edges = [
        WorkflowEdge(source_node_id="N-TRIG", target_node_id="N-SEC"),
        WorkflowEdge(source_node_id="N-SEC", target_node_id="N-ACT"),
    ]
    wf = composer.create_workflow("ORG-TEST", "WS-CORP", "Sim WF", TriggerType.EVENT, nodes, edges)

    # Simulate with SAFE payload
    sim_safe = composer.simulate_workflow(wf.workflow_id, {"security_state": "SAFE"})
    assert sim_safe.is_simulation is True
    assert len(sim_safe.nodes_executed) == 3
    assert len(sim_safe.proposed_actions) == 1
    assert "N-ACT" in sim_safe.approvals_required

    # Simulate with HIGH_RISK payload -> Halts at security scan
    sim_risk = composer.simulate_workflow(wf.workflow_id, {"security_state": "HIGH_RISK"})
    assert len(sim_risk.nodes_executed) == 2
    assert len(sim_risk.proposed_actions) == 0


# =========================================================================
# 3. GOVERNED EXECUTION, SECURITY BARRIER & APPROVAL GATE
# =========================================================================

def test_workflow_governed_execution():
    """Verifies deterministic execution, security blocks, approval gates, and multi-tenant scoping."""
    composer = EnterpriseWorkflowComposer()

    nodes = [
        WorkflowNode(node_id="N-TRIG", node_type=NodeType.TRIGGER, capability_name="EventTrigger"),
        WorkflowNode(node_id="N-SEC", node_type=NodeType.SECURITY_SCAN, capability_name="SecurityAgent"),
        WorkflowNode(node_id="N-ACT", node_type=NodeType.ACTION, capability_name="ATS_WRITE", is_high_impact=True),
    ]
    edges = [
        WorkflowEdge(source_node_id="N-TRIG", target_node_id="N-SEC"),
        WorkflowEdge(source_node_id="N-SEC", target_node_id="N-ACT"),
    ]
    wf = composer.create_workflow("ORG-ALPHA", "WS-CORP", "Gov WF", TriggerType.EVENT, nodes, edges)

    # 1. Unapproved/Draft Execution -> Fails because workflow is not ACTIVE
    run_draft = composer.execute_workflow(wf.workflow_id, {"security_state": "SAFE"})
    assert run_draft.status == RunStatus.FAILED

    # Activate workflow
    assert composer.approve_and_activate(wf.workflow_id, "BOARD") is True

    # 2. Security Barrier: HIGH_RISK -> Halts execution
    run_risk = composer.execute_workflow(wf.workflow_id, {"security_state": "HIGH_RISK"})
    assert run_risk.status == RunStatus.FAILED
    assert "Security Gate Barrier" in run_risk.error_message

    # 3. High-Impact Action without pre-approval -> WAITING_FOR_APPROVAL
    run_app = composer.execute_workflow(wf.workflow_id, {"security_state": "SAFE", "is_pre_approved": False})
    assert run_app.status == RunStatus.WAITING_FOR_APPROVAL

    # 4. Pre-approved Execution -> COMPLETED
    run_success = composer.execute_workflow(wf.workflow_id, {"security_state": "SAFE", "is_pre_approved": True})
    assert run_success.status == RunStatus.COMPLETED

    # 5. Global Pause Switch -> PAUSED
    composer.set_global_automation_paused(True)
    run_paused = composer.execute_workflow(wf.workflow_id, {"security_state": "SAFE"})
    assert run_paused.status == RunStatus.PAUSED

    # 6. Tenant Isolation: Org Beta cannot see Org Alpha workflows
    assert len(composer.get_workflows("ORG-BETA")) == 0
    assert len(composer.get_workflows("ORG-ALPHA")) == 1
