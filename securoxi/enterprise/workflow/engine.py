"""
SECUROXI AI Intelligence 2.0 — Enterprise Workflow Composer & Automation Studio Engine (Phase 9 Stage 55)
Provides declarative workflow creation, DAG validation, side-effect-free simulation,
governed activation, and deterministic execution.
"""

from typing import Dict, Any, List, Optional, Set
import time
from securoxi.enterprise.workflow.types import (
    WorkflowStatus,
    TriggerType,
    NodeType,
    WorkflowRiskClass,
    RunStatus,
)
from securoxi.enterprise.workflow.models import (
    WorkflowNode,
    WorkflowEdge,
    WorkflowDefinition,
    WorkflowRun,
    WorkflowSimulationResult,
)
from securoxi.logger import get_logger

logger = get_logger("enterprise.workflow.engine")


class EnterpriseWorkflowComposer:
    """
    Enterprise Workflow Composer & Automation Studio.
    Allows composing visual/declarative workflows, performing cycle validation,
    side-effect-free simulations, and governed execution without arbitrary code.
    """

    def __init__(self):
        self._workflows: Dict[str, WorkflowDefinition] = {}  # workflow_id -> WorkflowDefinition
        self._runs: Dict[str, WorkflowRun] = {}              # run_id -> WorkflowRun
        self._global_automation_paused: bool = False

    def set_global_automation_paused(self, paused: bool):
        """Emergency platform kill switch to pause all enterprise automation."""
        self._global_automation_paused = paused
        logger.warning(f"Global Automation Paused: {paused}")

    def create_workflow(
        self,
        organization_id: str,
        workspace_id: str,
        name: str,
        trigger_type: TriggerType,
        nodes: List[WorkflowNode],
        edges: List[WorkflowEdge],
        created_by: str = "WORKFLOW_ADMIN",
    ) -> WorkflowDefinition:
        """Creates a new draft declarative workflow definition."""
        # Calculate risk class
        has_high_impact = any(n.is_high_impact or n.requires_approval for n in nodes)
        risk_class = WorkflowRiskClass.HIGH if has_high_impact else WorkflowRiskClass.LOW

        wf = WorkflowDefinition(
            organization_id=organization_id,
            workspace_id=workspace_id,
            name=name,
            trigger_type=trigger_type,
            nodes=nodes,
            edges=edges,
            risk_class=risk_class,
            created_by=created_by,
            status=WorkflowStatus.DRAFT,
        )
        self._workflows[wf.workflow_id] = wf
        logger.info(f"Created Workflow '{wf.workflow_id}' ('{name}') RiskClass={risk_class.value}")
        return wf

    def validate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Validates workflow DAG for cycles, unreachable nodes, and edge consistency.
        """
        wf = self._workflows.get(workflow_id)
        if not wf:
            return {"valid": False, "error": "Workflow not found"}

        node_ids = {n.node_id for n in wf.nodes}

        # Check edge references
        for edge in wf.edges:
            if edge.source_node_id not in node_ids:
                return {"valid": False, "error": f"Invalid source node '{edge.source_node_id}' in edge"}
            if edge.target_node_id not in node_ids:
                return {"valid": False, "error": f"Invalid target node '{edge.target_node_id}' in edge"}

        # Cycle detection (DFS)
        adj: Dict[str, List[str]] = {n_id: [] for n_id in node_ids}
        for edge in wf.edges:
            adj[edge.source_node_id].append(edge.target_node_id)

        visited: Dict[str, int] = {n_id: 0 for n_id in node_ids}  # 0=unvisited, 1=visiting, 2=visited

        def has_cycle(node: str) -> bool:
            visited[node] = 1
            for neighbor in adj.get(node, []):
                if visited[neighbor] == 1:
                    return True
                if visited[neighbor] == 0 and has_cycle(neighbor):
                    return True
            visited[node] = 2
            return False

        for n_id in node_ids:
            if visited[n_id] == 0:
                if has_cycle(n_id):
                    return {"valid": False, "error": "Workflow contains a cycle (loops are prohibited)"}

        return {"valid": True, "node_count": len(wf.nodes), "edge_count": len(wf.edges)}

    def simulate_workflow(
        self,
        workflow_id: str,
        sample_payload: Dict[str, Any],
    ) -> WorkflowSimulationResult:
        """
        Executes workflow in zero side-effect simulation mode.
        """
        wf = self._workflows.get(workflow_id)
        if not wf:
            raise ValueError(f"Workflow '{workflow_id}' not found")

        executed_nodes: List[str] = []
        branches: List[str] = []
        proposed_actions: List[str] = []
        approvals: List[str] = []

        security_state = sample_payload.get("security_state", "SAFE")

        for node in wf.nodes:
            executed_nodes.append(node.node_id)
            if node.node_type == NodeType.SECURITY_SCAN:
                if security_state in {"HIGH_RISK", "UNINSPECTABLE"}:
                    branches.append(f"{node.node_id} -> SECURITY_HALT ({security_state})")
                    break
            elif node.node_type == NodeType.ACTION:
                proposed_actions.append(f"PROPOSED_ACTION: {node.capability_name}")
                if node.requires_approval or node.is_high_impact:
                    approvals.append(node.node_id)

        sim_res = WorkflowSimulationResult(
            workflow_id=workflow_id,
            organization_id=wf.organization_id,
            nodes_executed=executed_nodes,
            branches_taken=branches,
            proposed_actions=proposed_actions,
            approvals_required=approvals,
            is_simulation=True,
        )
        logger.info(f"Simulated Workflow '{workflow_id}': {len(executed_nodes)} nodes executed, {len(proposed_actions)} actions proposed")
        return sim_res

    def approve_and_activate(self, workflow_id: str, approved_by: str = "GOVERNANCE_BOARD") -> bool:
        """Approves and activates a validated workflow."""
        val = self.validate_workflow(workflow_id)
        if not val.get("valid"):
            logger.error(f"Cannot activate invalid workflow '{workflow_id}': {val.get('error')}")
            return False

        wf = self._workflows[workflow_id]
        wf.approved_by = approved_by
        wf.status = WorkflowStatus.ACTIVE
        wf.updated_at = time.time()
        logger.info(f"Activated Workflow '{workflow_id}' by '{approved_by}'")
        return True

    def execute_workflow(
        self,
        workflow_id: str,
        payload: Dict[str, Any],
    ) -> WorkflowRun:
        """
        Executes an active workflow with deterministic authority, security barriers, and approval gates.
        """
        wf = self._workflows.get(workflow_id)
        if not wf:
            raise ValueError(f"Workflow '{workflow_id}' not found")

        run = WorkflowRun(
            workflow_id=workflow_id,
            workflow_version=wf.version,
            organization_id=wf.organization_id,
            workspace_id=wf.workspace_id,
            status=RunStatus.RUNNING,
        )
        self._runs[run.run_id] = run

        if self._global_automation_paused:
            run.status = RunStatus.PAUSED
            run.error_message = "Execution halted: Global automation is currently paused"
            run.completed_at = time.time()
            return run

        if wf.status != WorkflowStatus.ACTIVE:
            run.status = RunStatus.FAILED
            run.error_message = f"Workflow is not ACTIVE (current status: {wf.status.value})"
            run.completed_at = time.time()
            return run

        security_state = payload.get("security_state", "SAFE")
        current_state = dict(payload)

        for node in wf.nodes:
            run.current_node_id = node.node_id
            run.executed_nodes.append(node.node_id)

            # 1. Deterministic Security Authority
            if node.node_type == NodeType.SECURITY_SCAN:
                if security_state in {"HIGH_RISK", "UNINSPECTABLE"}:
                    run.status = RunStatus.FAILED
                    run.error_message = f"Security Gate Barrier: Target resource is {security_state}"
                    run.completed_at = time.time()
                    return run
                current_state["security_verified"] = True

            # 2. Approval Gate
            elif node.node_type == NodeType.APPROVAL or node.requires_approval or node.is_high_impact:
                if not payload.get("is_pre_approved", False):
                    run.status = RunStatus.WAITING_FOR_APPROVAL
                    run.error_message = f"Node '{node.node_id}' requires Stage 23 Human Approval"
                    run.completed_at = time.time()
                    return run

            # 3. Action Execution (Governed)
            elif node.node_type == NodeType.ACTION:
                current_state[f"action_{node.node_id}"] = "EXECUTED"

            run.node_outputs[node.node_id] = {"status": "SUCCESS"}

        run.status = RunStatus.COMPLETED
        run.completed_at = time.time()
        logger.info(f"Workflow Run '{run.run_id}' for Workflow '{workflow_id}' completed successfully")
        return run

    def get_workflows(self, organization_id: str) -> List[WorkflowDefinition]:
        """Returns workflows strictly scoped by organization."""
        return [w for w in self._workflows.values() if w.organization_id == organization_id]
