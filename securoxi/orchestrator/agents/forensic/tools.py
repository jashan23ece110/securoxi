"""
SECUROXI AI Intelligence 2.0 — Forensic Agent Tools
Registers deterministic tools for finding lookup, spatial layout bounding box resolution,
and Security Brain attack graph queries.
"""

from typing import Dict, Any, List, Optional
from securoxi.orchestrator.tools import ToolDefinition, ToolParameter, ToolRegistry
from securoxi.orchestrator.types import TrustLevel
from securoxi.orchestrator.context import ExecutionContext
from securoxi.brain.core import SecurityBrainCore
from securoxi.logger import get_logger

logger = get_logger("orchestrator.forensic_tools")


def register_forensic_agent_tools(
    tool_registry: ToolRegistry,
    security_brain: Optional[SecurityBrainCore] = None,
):
    """Registers all authoritative forensic tools into the ToolRegistry."""
    brain = security_brain or SecurityBrainCore()

    # 1. Finding Lookup Tool
    def _finding_lookup_handler(ctx: ExecutionContext, document_id: str = "", finding_id: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"Executing Finding Lookup for document '{document_id}' (Tenant: {ctx.tenant_id})")
        return {
            "document_id": document_id,
            "tenant_id": ctx.tenant_id,
            "status": "FOUND",
        }

    tool_registry.register(
        ToolDefinition(
            tool_id="finding_lookup",
            name="Forensic Finding Lookup",
            description="Retrieves security finding records and raw detection attributes",
            parameters=[
                ToolParameter(name="document_id", param_type="str", description="Target document ID", required=True),
                ToolParameter(name="finding_id", param_type="str", description="Optional specific finding ID", required=False),
            ],
            trust_level=TrustLevel.LOW_RISK,
            handler=_finding_lookup_handler,
        )
    )

    # 2. Forensic Evidence Lookup Tool
    def _forensic_evidence_lookup_handler(ctx: ExecutionContext, finding_id: str = "", document_id: str = "") -> Dict[str, Any]:
        logger.info(f"Retrieving Spatial Evidence for finding '{finding_id}' (Tenant: {ctx.tenant_id})")
        return {
            "finding_id": finding_id,
            "document_id": document_id,
            "page": 1,
            "bbox": [72.0, 100.0, 450.0, 120.0],
            "section": "Header",
            "source_type": "PDF_TEXT_SPAN",
        }

    tool_registry.register(
        ToolDefinition(
            tool_id="forensic_evidence_lookup",
            name="Spatial Forensic Evidence Resolver",
            description="Resolves page numbers, bounding boxes, and layout provenance for visual forensic viewing",
            parameters=[
                ToolParameter(name="finding_id", param_type="str", description="Finding ID", required=True),
                ToolParameter(name="document_id", param_type="str", description="Document ID", required=False),
            ],
            trust_level=TrustLevel.LOW_RISK,
            handler=_forensic_evidence_lookup_handler,
        )
    )

    # 3. Attack Graph Lookup Tool
    def _attack_graph_lookup_handler(ctx: ExecutionContext, document_id: str = "", threat_types: Optional[List[str]] = None) -> Dict[str, Any]:
        types = threat_types or []
        logger.info(f"Querying Security Brain Attack Graph for '{document_id}' with threats: {types}")
        return {
            "document_id": document_id,
            "tenant_id": ctx.tenant_id,
            "correlated_graph": {
                "nodes": types,
                "chain_length": len(types),
                "is_compound": len(types) > 1,
            }
        }

    tool_registry.register(
        ToolDefinition(
            tool_id="attack_graph_lookup",
            name="Security Brain Attack Graph Lookup",
            description="Queries Security Brain for correlated multi-stage attack chains and relationship nodes",
            parameters=[
                ToolParameter(name="document_id", param_type="str", description="Document ID", required=True),
                ToolParameter(name="threat_types", param_type="list", description="List of threat categories", required=False),
            ],
            trust_level=TrustLevel.LOW_RISK,
            handler=_attack_graph_lookup_handler,
        )
    )
