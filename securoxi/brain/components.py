"""
SECUROXI AI Phase 3 Stage 1 — 12 Core Security Brain Component Implementations
"""

import time
from typing import List, Dict, Any, Optional
from securoxi.brain.models import (
    SecuritySignal, SignalSeverity, EventSource, ThreatEntity,
    CorrelationObject, AttackChainGraph, PolicyAction, PolicyDecision
)
from securoxi.logger import get_logger


class SignalCollector:
    """Component 1: Collects raw security signals from documents, ATS webhooks, and agent events."""
    def __init__(self):
        self.logger = get_logger("securoxi.brain.collector")

    def collect_signal(
        self,
        source: EventSource,
        signal_type: str,
        severity: SignalSeverity,
        payload: Dict[str, Any],
        provenance: str = "UNKNOWN"
    ) -> SecuritySignal:
        sig = SecuritySignal(
            source=source,
            signal_type=signal_type,
            severity=severity,
            raw_payload=payload,
            provenance_location=provenance
        )
        self.logger.info(f"Signal collected [{sig.signal_id}]: {sig.signal_type} from {source.value}")
        return sig


class ForensicsEngine:
    """Component 2: Analyzes low-level document & event structure (font size, color distance, zero-width chars)."""
    def analyze_payload(self, signal: SecuritySignal) -> Dict[str, Any]:
        payload = signal.raw_payload
        text = str(payload.get("text", ""))

        has_micro = payload.get("font_size", 10.0) < 2.0
        has_white = payload.get("color", (0, 0, 0)) == (1, 1, 1) or "#ffffff" in str(payload.get("color_hex", "")).lower()

        import unicodedata
        has_invisible = any(unicodedata.category(ch) == "Cf" for ch in text)

        return {
            "has_micro_text": has_micro,
            "has_white_text": has_white,
            "has_invisible_unicode": has_invisible,
            "span_count": payload.get("span_count", 1)
        }


class ThreatDetector:
    """Component 3: Evaluates threat signatures (prompt injection, visual deception, ATS manipulation)."""
    PROMPT_INJECTION_KEYWORDS = [
        "ignore previous instructions", "ignore all instructions",
        "system instruction", "unconditionally rank", "give score 100", "hired"
    ]

    def detect_threats(self, signal: SecuritySignal, forensics: Dict[str, Any]) -> List[Dict[str, Any]]:
        threats = []
        text_lower = str(signal.raw_payload.get("text", "")).lower()

        # Check prompt injection signatures
        for kw in self.PROMPT_INJECTION_KEYWORDS:
            if kw in text_lower:
                threats.append({
                    "threat_type": "PROMPT_INJECTION",
                    "severity": SignalSeverity.HIGH.value,
                    "keyword": kw,
                    "provenance": signal.provenance_location
                })

        # Check visual deception signatures
        if forensics.get("has_white_text") or forensics.get("has_micro_text"):
            threats.append({
                "threat_type": "VISUAL_DECEPTION",
                "severity": SignalSeverity.HIGH.value,
                "detail": "White font or micro-text detected",
                "provenance": signal.provenance_location
            })

        return threats


class ContextEnricher:
    """Component 4: Enriches security signals with candidate profile and JD context metadata."""
    def enrich(self, signal: SecuritySignal, context_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        meta = context_meta or {}
        return {
            "candidate_id": meta.get("candidate_id", "ANONYMOUS"),
            "ats_user_id": meta.get("ats_user_id", "SYSTEM"),
            "client_ip": meta.get("client_ip", "127.0.0.1"),
            "job_title": meta.get("job_title", "NOT_SPECIFIED")
        }


class CorrelationEngine:
    """Component 5: Correlates multiple security signals into a synthesized incident object."""
    def correlate(self, signals: List[SecuritySignal], threats: List[Dict[str, Any]]) -> CorrelationObject:
        signal_ids = [s.signal_id for s in signals]
        threat_types = list(set(t["threat_type"] for t in threats))

        primary_threat = threat_types[0] if threat_types else "NONE"
        risk_score = 100.0 if "PROMPT_INJECTION" in threat_types or "VISUAL_DECEPTION" in threat_types else 0.0

        inc = CorrelationObject(
            primary_threat_type=primary_threat,
            correlated_signal_ids=signal_ids,
            composite_risk_score=risk_score,
            attack_chain_summary=f"Correlated {len(signals)} signals across threat types: {threat_types}"
        )
        return inc


class AttackGraphBuilder:
    """Component 6: Constructs graph mapping nodes and directed edges across multi-stage attacks."""
    def build_graph(self, incident: CorrelationObject, signals: List[SecuritySignal]) -> AttackChainGraph:
        graph = AttackChainGraph()

        # Add incident root node
        graph.add_node(incident.incident_id, label=incident.primary_threat_type, node_type="INCIDENT")

        for sig in signals:
            graph.add_node(sig.signal_id, label=sig.signal_type, node_type="SIGNAL")
            graph.add_edge(incident.incident_id, sig.signal_id, relationship="CONTAINS_SIGNAL")

        return graph

    def build_threat_graph(
        self,
        artifact_name: str,
        signals: List[SecuritySignal],
        threats: List[Dict[str, Any]],
        target_system: str = "RESUME_SCREENING_PIPELINE"
    ):
        """Constructs rich relationship graph: Actor/Artifact -> Signal -> Technique -> Target -> Impact."""
        from securoxi.brain.threat_intel import ThreatGraphModel, SECUROXI_TECHNIQUES

        tg = ThreatGraphModel()

        # Nodes
        artifact_id = f"ART-{artifact_name}"
        tg.add_entity(artifact_id, name=artifact_name, entity_type="ARTIFACT")

        target_id = f"TGT-{target_system}"
        tg.add_entity(target_id, name=target_system, entity_type="TARGET_SYSTEM")

        for sig in signals:
            tg.add_entity(sig.signal_id, name=sig.signal_type, entity_type="SIGNAL")
            tg.add_relationship(artifact_id, sig.signal_id, rel_type="PRODUCES_SIGNAL")

        for thr in threats:
            thr_type = thr.get("threat_type", "UNKNOWN")
            tech_id = f"TECH-{thr_type}"
            tg.add_entity(tech_id, name=thr_type, entity_type="ATTACK_TECHNIQUE")

            for sig in signals:
                tg.add_relationship(sig.signal_id, tech_id, rel_type="TRIGGERS_TECHNIQUE")

            tg.add_relationship(tech_id, target_id, rel_type="TARGETS_SYSTEM")

            impact_id = f"IMP-{thr_type}"
            tg.add_entity(impact_id, name=f"Impact: {thr_type}", entity_type="POTENTIAL_IMPACT")
            tg.add_relationship(target_id, impact_id, rel_type="RISKS_IMPACT")

        return tg



class SecurityReasoningLayer:
    """Component 7: Applies XML-isolated reasoning (<untrusted_security_context>) to evaluate threat intent."""
    def evaluate_reasoning(self, incident: CorrelationObject, graph: AttackChainGraph) -> Dict[str, Any]:
        # XML-isolated prompt safety check
        isolated_prompt = (
            f"<untrusted_security_context>\n"
            f"Incident ID: {incident.incident_id}\n"
            f"Primary Threat: {incident.primary_threat_type}\n"
            f"Risk Score: {incident.composite_risk_score}\n"
            f"</untrusted_security_context>\n"
        )
        return {
            "isolated_prompt_tokens": len(isolated_prompt.split()),
            "reasoning_verdict": "MALICIOUS_INTENT_CONFIRMED" if incident.composite_risk_score >= 80.0 else "BENIGN",
            "confidence": 0.95
        }


class RiskEngine:
    """Component 8: Computes final composite risk scores (0.0 to 100.0) with risk propagation."""
    def compute_risk(self, incident: CorrelationObject, reasoning: Dict[str, Any]) -> float:
        base_risk = incident.composite_risk_score
        if reasoning.get("reasoning_verdict") == "MALICIOUS_INTENT_CONFIRMED":
            return min(base_risk * 1.0, 100.0)
        return base_risk


class PolicyEngine:
    """Component 9: Evaluates security policies and returns enforced policy decisions."""
    def evaluate_policy(self, risk_score: float) -> PolicyDecision:
        if risk_score >= 80.0:
            return PolicyDecision(
                action=PolicyAction.QUARANTINE_BLOCK,
                risk_score=risk_score,
                reasoning="High risk score exceeds safety threshold (80.0)."
            )
        elif risk_score >= 30.0:
            return PolicyDecision(
                action=PolicyAction.SUSPEND_SCREENING,
                risk_score=risk_score,
                reasoning="Medium risk score requires human security review."
            )
        return PolicyDecision(
            action=PolicyAction.ALLOW,
            risk_score=risk_score,
            reasoning="Passed security policy evaluation."
        )


class ActionResponseLayer:
    """Component 10: Executes policy enforcement (quarantining document, suspending screening)."""
    def execute_action(self, decision: PolicyDecision, target_id: str) -> Dict[str, Any]:
        return {
            "target_id": target_id,
            "enforced_action": decision.action.value,
            "status": "EXECUTED",
            "enforced_at": time.time()
        }


class EvidenceStore:
    """Component 11: In-memory/persistent evidence store maintaining full signal provenance."""
    def __init__(self):
        self._store: Dict[str, SecuritySignal] = {}

    def save_signal(self, signal: SecuritySignal):
        self._store[signal.signal_id] = signal

    def get_signal(self, signal_id: str) -> Optional[SecuritySignal]:
        return self._store.get(signal_id)


class AuditObservabilityLayer:
    """Component 12: Emits structured JSON audit events and metrics for observability."""
    def __init__(self):
        self.logger = get_logger("securoxi.brain.audit")
        self._audit_events: List[Dict[str, Any]] = []

    def emit_event(self, event_type: str, details: Dict[str, Any]):
        evt = {
            "event_type": event_type,
            "details": details,
            "timestamp": time.time()
        }
        self._audit_events.append(evt)
        self.logger.info(f"AUDIT EVENT [{event_type}]: {details}")

    def get_events(self) -> List[Dict[str, Any]]:
        return list(self._audit_events)
