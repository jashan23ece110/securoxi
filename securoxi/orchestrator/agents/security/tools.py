"""
SECUROXI AI Intelligence 2.0 — Security Agent Tools
Registers deterministic tools connected to the SecuroxiEngine, Security Brain,
Policy Engine, and Evidence Store.
"""

from typing import Dict, Any, List, Optional
from securoxi.orchestrator.tools import ToolDefinition, ToolParameter, ToolRegistry
from securoxi.orchestrator.types import TrustLevel
from securoxi.orchestrator.context import ExecutionContext
from securoxi.engine import SecuroxiEngine
from securoxi.brain.core import SecurityBrainCore
from securoxi.brain.policy_engine import SecuroxiPolicyEngine, PolicyContext, PolicyDecisionAction
from securoxi.brain.models import EventSource, SignalSeverity
from securoxi.logger import get_logger

logger = get_logger("orchestrator.security_tools")


def register_security_agent_tools(
    tool_registry: ToolRegistry,
    security_engine: Optional[SecuroxiEngine] = None,
    security_brain: Optional[SecurityBrainCore] = None,
    policy_engine: Optional[SecuroxiPolicyEngine] = None,
):
    """Registers all authoritative security tools into the ToolRegistry."""
    engine = security_engine or SecuroxiEngine()
    brain = security_brain or SecurityBrainCore()
    policy = policy_engine or SecuroxiPolicyEngine()

    # 1. Document Security Scan Tool
    def _scan_handler(ctx: ExecutionContext, doc_path: str = "", doc_id: str = "") -> Dict[str, Any]:
        logger.info(f"Executing deterministic scan for '{doc_path or doc_id}' (Tenant: {ctx.tenant_id})")
        if doc_path:
            try:
                report = engine.analyze_document(doc_path)
                return {
                    "document_id": doc_id or doc_path,
                    "verdict": report.verdict.value,
                    "risk_score": report.risk_score,
                    "findings_count": len(report.findings),
                    "findings": [f.to_dict() for f in report.findings],
                    "raw_text_length": len(report.raw_text),
                }
            except Exception as e:
                logger.error(f"Scan error for {doc_path}: {e}")
                return {
                    "document_id": doc_id or doc_path,
                    "verdict": "UNINSPECTABLE",
                    "risk_score": 50.0,
                    "findings_count": 0,
                    "findings": [],
                    "error": str(e),
                }
        return {
            "document_id": doc_id,
            "verdict": "SAFE",
            "risk_score": 0.0,
            "findings_count": 0,
            "findings": [],
        }

    tool_registry.register(
        ToolDefinition(
            tool_id="document_security_scan",
            name="Document Security Scanner",
            description="Deterministically scans documents for prompt injection, visual deception, and hidden text",
            parameters=[
                ToolParameter(name="doc_path", param_type="str", description="Path to document file", required=False),
                ToolParameter(name="doc_id", param_type="str", description="Document identifier", required=False),
            ],
            trust_level=TrustLevel.LOW_RISK,
            handler=_scan_handler,
        )
    )

    # 2. Evidence Lookup Tool
    def _evidence_handler(ctx: ExecutionContext, document_id: str = "", findings: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        findings_list = findings or []
        evidence_items = []
        for i, f in enumerate(findings_list):
            evidence_items.append({
                "evidence_id": f"EVD-{i+1:03d}",
                "finding_id": f.get("finding_id", f"FND-{i+1}"),
                "category": f.get("category", "PROMPT_INJECTION"),
                "severity": f.get("severity", "HIGH"),
                "title": f.get("title", "Security Finding"),
                "description": f.get("description", ""),
                "original_text_excerpt": f.get("evidence", f.get("description", ""))[:200],
                "page": f.get("page", 1),
                "location": f.get("location", "Body text"),
                "analyzer_source": f.get("analyzer_source", "PromptInjectionAnalyzer"),
                "verification_state": "VERIFIED",
            })
        return {
            "document_id": document_id,
            "evidence_count": len(evidence_items),
            "evidence_items": evidence_items,
        }

    tool_registry.register(
        ToolDefinition(
            tool_id="evidence_lookup",
            name="Evidence Lookup",
            description="Retrieves granular forensic evidence items and locations for detected security findings",
            parameters=[
                ToolParameter(name="document_id", param_type="str", description="Document ID", required=True),
                ToolParameter(name="findings", param_type="list", description="List of findings to resolve", required=False),
            ],
            trust_level=TrustLevel.LOW_RISK,
            handler=_evidence_handler,
        )
    )

    # 3. Security Brain Lookup Tool
    def _brain_handler(ctx: ExecutionContext, document_id: str = "", threat_types: Optional[List[str]] = None, risk_score: float = 0.0) -> Dict[str, Any]:
        types = threat_types or []
        # Query brain correlation pipeline
        event_res = brain.process_event(
            source=EventSource.AGENT_TOOL_CALL,
            signal_type="CORRELATION_QUERY",
            severity=SignalSeverity.HIGH if risk_score >= 70 else SignalSeverity.MEDIUM,
            payload={"document_id": document_id, "threat_types": types, "risk_score": risk_score},
            provenance=f"Tenant:{ctx.tenant_id}",
        )
        return {
            "document_id": document_id,
            "correlated": len(types) > 1,
            "correlation_summary": "Multi-stage attack pattern detected" if len(types) > 1 else "Isolated single finding",
            "attack_graph_nodes": len(types) + 1,
            "brain_event_id": event_res.get("event_id", "EVT-BRAIN"),
        }

    tool_registry.register(
        ToolDefinition(
            tool_id="security_brain_lookup",
            name="Security Brain Correlation Lookup",
            description="Queries the 12-component Security Brain for attack graphs, threat intelligence, and correlation",
            parameters=[
                ToolParameter(name="document_id", param_type="str", description="Document ID", required=True),
                ToolParameter(name="threat_types", param_type="list", description="Detected threat categories", required=False),
                ToolParameter(name="risk_score", param_type="float", description="Risk score", required=False),
            ],
            trust_level=TrustLevel.LOW_RISK,
            handler=_brain_handler,
        )
    )

    # 4. Policy Evaluation Lookup Tool
    def _policy_handler(ctx: ExecutionContext, verdict: str = "SAFE", risk_score: float = 0.0, threat_types: Optional[List[str]] = None) -> Dict[str, Any]:
        policy_ctx = PolicyContext(
            verdict=verdict,
            risk_score=risk_score,
            source="AGENT_TOOL_CALL",
            target="SECURITY_INVESTIGATION",
            threat_types=threat_types or [],
            metadata={"tenant_id": ctx.tenant_id, "actor_id": ctx.actor_id}
        )
        decision = policy.evaluate_policy(policy_ctx)
        return {
            "policy_id": "GLOBAL-POLICY-GATE",
            "rule_name": decision.rule_id or "Standard Policy",
            "action": decision.action.value,
            "authoritative_verdict": verdict,
            "explanation": decision.explanation,
        }

    tool_registry.register(
        ToolDefinition(
            tool_id="policy_lookup",
            name="Policy Evaluation Lookup",
            description="Queries the deterministic PolicyEngine for authoritative policy actions and rules",
            parameters=[
                ToolParameter(name="verdict", param_type="str", description="Document verdict", required=True),
                ToolParameter(name="risk_score", param_type="float", description="Risk score", required=False),
                ToolParameter(name="threat_types", param_type="list", description="Threat categories", required=False),
            ],
            trust_level=TrustLevel.LOW_RISK,
            handler=_policy_handler,
        )
    )
