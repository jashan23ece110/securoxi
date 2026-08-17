"""
SECUROXI AI Phase 3 Stage 1 — Security Brain Core Orchestration Engine
Unifies all 12 modular security brain components into a single enterprise architecture pipeline:
Event -> Forensics -> Detection -> Context -> Correlation -> Attack Graph -> Reasoning -> Risk -> Policy -> Action -> Evidence -> Audit
"""

from typing import Dict, Any, Optional
from securoxi.config import SecuroxiConfig
from securoxi.logger import get_logger
from securoxi.brain.models import EventSource, SignalSeverity
from securoxi.brain.components import (
    SignalCollector, ForensicsEngine, ThreatDetector, ContextEnricher,
    CorrelationEngine, AttackGraphBuilder, SecurityReasoningLayer,
    RiskEngine, PolicyEngine, ActionResponseLayer, EvidenceStore,
    AuditObservabilityLayer
)


class SecurityBrainCore:
    """
    Unified 12-Component Enterprise Security Brain Architecture.
    Orchestrates end-to-end security reasoning across documents, ATS webhooks, and agent events.
    """

    def __init__(self, config: Optional[SecuroxiConfig] = None):
        self.config = config or SecuroxiConfig()
        self.logger = get_logger("securoxi.brain.core")

        # Instantiate 12 Modular Components
        self.collector = SignalCollector()
        self.forensics = ForensicsEngine()
        self.detector = ThreatDetector()
        self.enricher = ContextEnricher()
        self.correlation = CorrelationEngine()
        self.attack_graph = AttackGraphBuilder()
        self.reasoning = SecurityReasoningLayer()
        self.risk_engine = RiskEngine()
        self.policy_engine = PolicyEngine()
        self.action_layer = ActionResponseLayer()
        self.evidence_store = EvidenceStore()
        self.audit_layer = AuditObservabilityLayer()

    def process_event(
        self,
        source: EventSource,
        signal_type: str,
        severity: SignalSeverity,
        payload: Dict[str, Any],
        provenance: str = "UNKNOWN",
        context_meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute 12-Step Security Brain Pipeline:
        1. Collector -> 2. Forensics -> 3. Threat Detection -> 4. Context ->
        5. Correlation -> 6. Attack Graph -> 7. Security Reasoning ->
        8. Risk Engine -> 9. Policy Engine -> 10. Action Layer -> 11. Evidence Store -> 12. Audit
        """
        self.logger.info(f"Security Brain processing event from '{source.value}' ({signal_type})")

        # Step 1: Collect Signal
        sig = self.collector.collect_signal(source, signal_type, severity, payload, provenance)

        # Step 2: Content & Structure Forensics
        forensic_res = self.forensics.analyze_payload(sig)

        # Step 3: Threat Detection Signatures
        threats = self.detector.detect_threats(sig, forensic_res)

        # Step 4: Context Enrichment
        enriched_ctx = self.enricher.enrich(sig, context_meta)

        # Step 5: Correlation Engine
        incident = self.correlation.correlate([sig], threats)

        # Step 6: Attack Chain Graph & Threat Graph Construction
        graph = self.attack_graph.build_graph(incident, [sig])
        threat_graph = self.attack_graph.build_threat_graph(provenance, [sig], threats)

        # Step 7: XML-Isolated Security Reasoning
        reasoning_res = self.reasoning.evaluate_reasoning(incident, graph)

        # Step 8: Risk Engine Propagation
        final_risk = self.risk_engine.compute_risk(incident, reasoning_res)

        # Step 9: Policy Engine Decision
        decision = self.policy_engine.evaluate_policy(final_risk)

        # Step 10: Action / Response Layer Execution
        action_res = self.action_layer.execute_action(decision, target_id=sig.signal_id)

        # Step 11: Save to Evidence Store
        self.evidence_store.save_signal(sig)

        # Step 12: Emit Audit Event
        self.audit_layer.emit_event(
            event_type="BRAIN_PIPELINE_EXECUTED",
            details={
                "signal_id": sig.signal_id,
                "incident_id": incident.incident_id,
                "threat_count": len(threats),
                "final_risk_score": final_risk,
                "action": decision.action.value
            }
        )

        return {
            "signal_id": sig.signal_id,
            "incident_id": incident.incident_id,
            "forensics": forensic_res,
            "threats": threats,
            "context": enriched_ctx,
            "attack_graph": graph.to_dict(),
            "threat_graph": threat_graph.to_dict(),
            "reasoning": reasoning_res,
            "final_risk_score": final_risk,
            "policy_decision": decision.to_dict(),
            "action_executed": action_res
        }

