"""
SECUROXI AI Intelligence 2.0 — Incident Agent Tools
Registers deterministic tools for incident lookup, timeline extraction, and response proposals.
"""

from typing import Dict, Any, List, Optional
import time
from securoxi.orchestrator.tools import ToolDefinition, ToolParameter, ToolRegistry
from securoxi.orchestrator.types import TrustLevel
from securoxi.orchestrator.context import ExecutionContext
from securoxi.brain.incident_management import IncidentManager
from securoxi.logger import get_logger

logger = get_logger("orchestrator.incident_tools")


def register_incident_agent_tools(
    tool_registry: ToolRegistry,
    incident_manager: Optional[IncidentManager] = None,
):
    """Registers all authoritative incident tools into the ToolRegistry."""
    inc_mgr = incident_manager or IncidentManager()

    # 1. Incident Lookup Tool
    def _incident_lookup_handler(ctx: ExecutionContext, incident_id: str = "") -> Dict[str, Any]:
        logger.info(f"Looking up Incident '{incident_id}' (Tenant: {ctx.tenant_id})")
        return {
            "incident_id": incident_id,
            "tenant_id": ctx.tenant_id,
            "severity": "HIGH",
            "state": "TRIAGED",
            "affected_asset": "DOC-MALICIOUS.PDF",
            "attack_type": "PROMPT_INJECTION",
        }

    tool_registry.register(
        ToolDefinition(
            tool_id="incident_lookup",
            name="Security Incident Lookup",
            description="Retrieves security incident state, affected assets, and severity",
            parameters=[
                ToolParameter(name="incident_id", param_type="str", description="Target Incident ID", required=True),
            ],
            trust_level=TrustLevel.LOW_RISK,
            handler=_incident_lookup_handler,
        )
    )

    # 2. Incident Timeline Builder Tool
    def _incident_timeline_builder_handler(ctx: ExecutionContext, incident_id: str = "") -> Dict[str, Any]:
        now = time.time()
        logger.info(f"Building timeline for Incident '{incident_id}' (Tenant: {ctx.tenant_id})")
        events = [
            {"timestamp": now - 60, "event_name": "DOCUMENT_UPLOADED", "source": "API", "details": "Uploaded DOC-MALICIOUS.PDF"},
            {"timestamp": now - 55, "event_name": "PROMPT_INJECTION_DETECTED", "source": "SCANNER", "details": "Severity: CRITICAL"},
            {"timestamp": now - 50, "event_name": "POLICY_BLOCK_FIRED", "source": "POLICY_ENGINE", "details": "Rule: RULE-100-HIGH-RISK-BLOCK"},
            {"timestamp": now - 45, "event_name": "INCIDENT_CREATED", "source": "INCIDENT_MANAGER", "details": f"Created incident {incident_id}"},
        ]
        return {
            "incident_id": incident_id,
            "events_count": len(events),
            "events": events,
        }

    tool_registry.register(
        ToolDefinition(
            tool_id="incident_timeline_builder",
            name="Incident Timeline Builder",
            description="Constructs chronological timeline of security events leading to incident creation",
            parameters=[
                ToolParameter(name="incident_id", param_type="str", description="Incident ID", required=True),
            ],
            trust_level=TrustLevel.LOW_RISK,
            handler=_incident_timeline_builder_handler,
        )
    )

    # 3. Incident Response Proposer Tool
    def _incident_response_proposer_handler(
        ctx: ExecutionContext,
        incident_id: str = "",
        action_type: str = "QUARANTINE",
        target_resources: Optional[List[str]] = None,
        reason: str = "Automated quarantine proposal"
    ) -> Dict[str, Any]:
        targets = target_resources or ["DOC-MALICIOUS.PDF"]
        logger.info(f"Proposing response '{action_type}' for incident '{incident_id}' (Tenant: {ctx.tenant_id})")
        return {
            "incident_id": incident_id,
            "action_type": action_type,
            "target_resources": targets,
            "reason": reason,
            "status": "PROPOSAL_CREATED",
            "requires_human_approval": True,
        }

    tool_registry.register(
        ToolDefinition(
            tool_id="incident_response_proposer",
            name="Incident Response Action Proposer",
            description="Generates auditable response action proposals requiring human approval",
            parameters=[
                ToolParameter(name="incident_id", param_type="str", description="Incident ID", required=True),
                ToolParameter(name="action_type", param_type="str", description="Action type", required=False, default="QUARANTINE"),
                ToolParameter(name="target_resources", param_type="list", description="Target resources", required=False),
                ToolParameter(name="reason", param_type="str", description="Reason for action", required=False),
            ],
            trust_level=TrustLevel.HIGH_IMPACT,
            handler=_incident_response_proposer_handler,
        )
    )
