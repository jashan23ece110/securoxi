"""
SECUROXI AI Intelligence 2.0 — Task Planner & DAG Converter
Translates structured TaskUnderstanding into declarative PlanNodeSpecs, validates
plans, and compiles them directly into executable Stage 1 ExecutionDAG instances.
"""

import time
import uuid
from typing import Dict, Any, List, Optional, Tuple

from securoxi.orchestrator.planning.types import (
    TaskIntent,
    PlanningStatus,
)
from securoxi.orchestrator.planning.models import (
    TaskUnderstanding,
    Plan,
    PlanNodeSpec,
)
from securoxi.orchestrator.planning.understanding import TaskUnderstandingEngine
from securoxi.orchestrator.planning.validator import PlanValidator
from securoxi.orchestrator.types import NodeType, ExecutionType, TrustLevel
from securoxi.orchestrator.graph import ExecutionNode, ExecutionDAG
from securoxi.orchestrator.tools import ToolRegistry
from securoxi.orchestrator.models import Task


class TaskPlanner:
    """
    High-level Task Planner generating validated execution plans and DAGs.
    """

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        understanding_engine: Optional[TaskUnderstandingEngine] = None,
        plan_validator: Optional[PlanValidator] = None,
    ):
        self.tools = tool_registry
        self.understanding_engine = understanding_engine or TaskUnderstandingEngine()
        self.validator = plan_validator or PlanValidator(self.tools)

    def plan_task(
        self,
        task: Task,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Plan, ExecutionDAG]:
        """
        Takes a Task, analyzes user intent, constructs a validated Plan,
        and compiles it into an executable ExecutionDAG for the Stage 1 Orchestrator.
        """
        ctx = context or task.context

        # 1. Natural Language Task Understanding
        understanding = self.understanding_engine.analyze_task(
            prompt=task.objective,
            tenant_id=task.tenant_id,
            actor_id=task.actor_id,
            available_context=ctx
        )

        # 2. Decompose into Plan Nodes based on Intent
        nodes = self._decompose_intent(understanding, task.task_id)

        # 3. Construct Plan
        plan = Plan(
            task_id=task.task_id,
            version=1,
            status=PlanningStatus.DRAFT,
            intent=understanding.primary_intent,
            objective=task.objective,
            understanding=understanding,
            nodes=nodes,
            dependencies={n.node_id: n.dependencies for n in nodes},
            estimated_runtime_sec=min(float(len(nodes) * 5), task.budget.max_runtime_sec),
            summary_explanation=understanding.objective_summary,
        )

        # 4. Deterministic Pre-Execution Validation
        self.validator.validate_plan(plan, tenant_id=task.tenant_id)

        # 5. Convert Plan to Stage 1 ExecutionDAG
        dag = self.convert_plan_to_dag(plan, run_id="")

        return plan, dag

    def _decompose_intent(
        self,
        u: TaskUnderstanding,
        task_id: str
    ) -> List[PlanNodeSpec]:
        """Decomposes structured understanding into dependency-linked PlanNodeSpecs."""
        nodes: List[PlanNodeSpec] = []

        if u.primary_intent in {TaskIntent.MIXED_WORKFLOW, TaskIntent.CANDIDATE_SCREENING}:
            # Node 1: Resolve Target JD & Candidate Pool
            n1 = PlanNodeSpec(
                name="resolve_inputs",
                node_type=NodeType.TRANSFORM,
                description="Resolve and verify authorized JD and candidate resume collection",
                execution_type=ExecutionType.DETERMINISTIC,
                trust_level=TrustLevel.LOW_RISK,
            )
            nodes.append(n1)

            # Node 2: Document Security Scan (CRITICAL SECURITY GATE)
            n2 = PlanNodeSpec(
                name="security_scan_documents",
                node_type=NodeType.TRANSFORM,
                description="Scan all candidate resumes for prompt injection, micro-text, and visual deception",
                dependencies=[n1.node_id],
                execution_type=ExecutionType.DETERMINISTIC,
                trust_level=TrustLevel.LOW_RISK,
            )
            nodes.append(n2)

            # Node 3: Security Filter (Exclude High-Risk)
            n3 = PlanNodeSpec(
                name="security_filter_gate",
                node_type=NodeType.DECISION,
                description="Enforce security policy: isolate and quarantine HIGH_RISK candidates",
                dependencies=[n2.node_id],
                execution_type=ExecutionType.DETERMINISTIC,
                trust_level=TrustLevel.CONTROLLED,
            )
            nodes.append(n3)

            # Node 4A & 4B: Parallel Extraction (Skills & Experience)
            n4a = PlanNodeSpec(
                name="extract_skills",
                node_type=NodeType.TRANSFORM,
                description="Extract required and preferred skills from safe candidate resumes",
                dependencies=[n3.node_id],
                is_parallelizable=True,
            )
            n4b = PlanNodeSpec(
                name="extract_experience",
                node_type=NodeType.TRANSFORM,
                description="Evaluate candidate years of experience against minimum threshold",
                dependencies=[n3.node_id],
                is_parallelizable=True,
            )
            nodes.extend([n4a, n4b])

            # Node 5: Compute Qualification & Ranking (Fan-in)
            n5 = PlanNodeSpec(
                name="screen_and_rank_candidates",
                node_type=NodeType.TRANSFORM,
                description=f"Calculate calibrated Fit Scores and rank top {u.target_count or 20} candidates",
                dependencies=[n4a.node_id, n4b.node_id],
                execution_type=ExecutionType.DETERMINISTIC,
                trust_level=TrustLevel.CONTROLLED,
            )
            nodes.append(n5)

            # Node 6: Finalize & Evidence Verification
            n6 = PlanNodeSpec(
                name="finalize_screening_report",
                node_type=NodeType.FINALIZE,
                description="Verify grounded evidence citations and assemble final candidate report",
                dependencies=[n5.node_id],
                execution_type=ExecutionType.DETERMINISTIC,
                trust_level=TrustLevel.LOW_RISK,
            )
            nodes.append(n6)

        elif u.primary_intent == TaskIntent.BULK_SCAN:
            n1 = PlanNodeSpec(
                name="discover_folder_files",
                node_type=NodeType.TRANSFORM,
                description="Discover and hash all files in selected directory",
            )
            n2 = PlanNodeSpec(
                name="streaming_security_scan",
                node_type=NodeType.TRANSFORM,
                description="Perform distributed streaming security inspection",
                dependencies=[n1.node_id],
            )
            n3 = PlanNodeSpec(
                name="finalize_distribution_summary",
                node_type=NodeType.FINALIZE,
                description="Aggregate scan verdict counts into SAFE, SUSPICIOUS, HIGH_RISK, UNINSPECTABLE",
                dependencies=[n2.node_id],
            )
            nodes.extend([n1, n2, n3])

        elif u.primary_intent == TaskIntent.QUESTION_ANSWERING:
            n1 = PlanNodeSpec(
                name="retrieve_authorized_chunks",
                node_type=NodeType.RETRIEVAL,
                description="Retrieve semantically relevant document chunks within tenant scope",
            )
            n2 = PlanNodeSpec(
                name="quarantine_verification",
                node_type=NodeType.VALIDATION,
                description="Verify retrieved chunks exclude quarantined malicious payloads",
                dependencies=[n1.node_id],
            )
            n3 = PlanNodeSpec(
                name="synthesize_grounded_answer",
                node_type=NodeType.FINALIZE,
                description="Generate natural language response with clickable citation cards",
                dependencies=[n2.node_id],
                execution_type=ExecutionType.AGENTIC,
            )
            nodes.extend([n1, n2, n3])

        else:
            # Default single document inspection flow
            n1 = PlanNodeSpec(
                name="parse_document",
                node_type=NodeType.TRANSFORM,
                description="Extract native text and structure from document",
            )
            n2 = PlanNodeSpec(
                name="security_analyzer",
                node_type=NodeType.TRANSFORM,
                description="Check for prompt injection and deceptive layout",
                dependencies=[n1.node_id],
            )
            n3 = PlanNodeSpec(
                name="finalize_report",
                node_type=NodeType.FINALIZE,
                description="Format scan report and determine clearance verdict",
                dependencies=[n2.node_id],
            )
            nodes.extend([n1, n2, n3])

        return nodes

    def convert_plan_to_dag(self, plan: Plan, run_id: str = "") -> ExecutionDAG:
        """Translates a Plan's declarative node specifications into an executable ExecutionDAG."""
        dag = ExecutionDAG(run_id=run_id)

        # Mapping from PlanNodeSpec.node_id -> ExecutionNode.node_id
        id_map: Dict[str, str] = {}

        for pnode in plan.nodes:
            exec_node = ExecutionNode(
                run_id=run_id,
                node_type=pnode.node_type,
                name=pnode.name,
                description=pnode.description,
                execution_type=pnode.execution_type,
                trust_level=pnode.trust_level,
                timeout_sec=pnode.timeout_sec,
                tool_id=pnode.tool_id,
                agent_id=pnode.agent_id,
                input_data=dict(pnode.input_bindings),
            )
            id_map[pnode.node_id] = exec_node.node_id
            dag.add_node(exec_node)

        # Connect dependencies using translated IDs
        for pnode in plan.nodes:
            exec_id = id_map[pnode.node_id]
            exec_node = dag.get_node(exec_id)
            if exec_node:
                translated_deps = [id_map[dep] for dep in pnode.dependencies if dep in id_map]
                exec_node.dependencies = translated_deps
                for dep_id in translated_deps:
                    if dep_id not in dag.edges:
                        dag.edges[dep_id] = []
                    if exec_id not in dag.edges[dep_id]:
                        dag.edges[dep_id].append(exec_id)

        return dag
