"""
SECUROXI AI Risk Correlation, Scoring & Verdict Engine
Aggregates security findings from VisualDeceptionAnalyzer and PromptInjectionAnalyzer,
evaluates span-level and nearby-span correlation boosts, computes 0-100 risk score,
and assigns final security verdict. Stage 2 Refined Engine.
"""

from typing import List, Dict, Any, Optional, Set
from securoxi.config import SecuroxiConfig
from securoxi.logger import get_logger
from securoxi.models import (
    SecurityFinding, AttackCategory, Severity, Verdict, AnalysisReport
)


class SecuroxiRiskEngine:
    """
    Deterministic risk correlation and verdict aggregation engine.
    Applies non-linear correlation rules to combine multi-modal threat signals.
    """

    VISUAL_CATEGORIES = {
        AttackCategory.MICRO_TEXT,
        AttackCategory.WHITE_TEXT,
        AttackCategory.BACKGROUND_MATCH,
        AttackCategory.HIDDEN_TEXT,
        AttackCategory.INVISIBLE_UNICODE,
        AttackCategory.SUSPICIOUS_POSITION,
        AttackCategory.VISUAL_DECEPTION
    }

    INJECTION_CATEGORIES = {
        AttackCategory.INSTRUCTION_OVERRIDE,
        AttackCategory.SYSTEM_PROMPT_MANIPULATION,
        AttackCategory.ATS_MANIPULATION,
        AttackCategory.AI_ROLE_MANIPULATION,
        AttackCategory.DATA_EXFILTRATION,
        AttackCategory.TOOL_MANIPULATION,
        AttackCategory.OBFUSCATION_INDICATORS,
        AttackCategory.PROMPT_INJECTION,
        AttackCategory.OBFUSCATION
    }

    def __init__(self, config: Optional[SecuroxiConfig] = None):
        self.config = config or SecuroxiConfig()
        self.logger = get_logger("securoxi.risk_engine")

    def evaluate(self, findings: List[SecurityFinding], filename: str = "document", doc_type: str = "PDF", total_spans: int = 0, execution_time_ms: float = 0.0) -> AnalysisReport:
        """
        Evaluate security findings, apply correlation boosts, compute score, and produce AnalysisReport.
        """

        if not findings:
            return AnalysisReport(
                filename=filename,
                document_type=doc_type,
                verdict=Verdict.SAFE,
                risk_score=0,
                primary_threat=None,
                overall_confidence=1.0,
                verdict_explanation="No security issues or deceptive patterns detected. Document appears SAFE.",
                findings=[],
                correlated_evidence=[],
                total_spans_analyzed=total_spans,
                execution_time_ms=execution_time_ms
            )

        # 1. Compute Base Category Weights
        raw_score = 0
        categories_detected: Set[AttackCategory] = set()

        for finding in findings:
            categories_detected.add(finding.category)
            weight = self.config.category_weights.get(finding.category, 20)
            raw_score += weight

        # 2. Evaluate Multi-Signal Correlation Boosts
        correlation_boost = 0
        correlated_evidence: List[str] = []

        # A. Same Span Overlap (Visual Deception + Prompt Injection on exact same text span location)
        span_locations: Dict[str, List[SecurityFinding]] = {}
        for finding in findings:
            loc = finding.location or "unknown"
            if loc not in span_locations:
                span_locations[loc] = []
            span_locations[loc].append(finding)

        for loc, loc_findings in span_locations.items():
            has_visual = any(f.category in self.VISUAL_CATEGORIES for f in loc_findings)
            has_injection = any(f.category in self.INJECTION_CATEGORIES for f in loc_findings)

            if has_visual and has_injection:
                boost = self.config.correlation_boosts.get("span_level_overlap", 20)
                correlation_boost += boost
                evidence_text = loc_findings[0].evidence[:50] if loc_findings[0].evidence else "N/A"
                correlated_evidence.append(
                    f"Visual Deception + Prompt Injection on same location ({loc}): \"{evidence_text}\" (+{boost} Risk)"
                )

        # B. Specific Compound Threat Pattern Correlation
        has_white_hidden = (AttackCategory.WHITE_TEXT in categories_detected or 
                            AttackCategory.HIDDEN_TEXT in categories_detected or
                            AttackCategory.MICRO_TEXT in categories_detected)
        
        has_ats = AttackCategory.ATS_MANIPULATION in categories_detected
        has_override = AttackCategory.INSTRUCTION_OVERRIDE in categories_detected
        has_exfil = AttackCategory.DATA_EXFILTRATION in categories_detected
        has_obfuscation = AttackCategory.OBFUSCATION_INDICATORS in categories_detected

        if has_white_hidden and has_ats:
            boost = self.config.correlation_boosts.get("white_hidden_plus_ats", 25)
            correlation_boost += boost
            correlated_evidence.append(f"Hidden/White Text + ATS Candidate Ranking Manipulation (+{boost} Risk)")

        if has_white_hidden and has_override:
            boost = self.config.correlation_boosts.get("white_hidden_plus_override", 20)
            correlation_boost += boost
            correlated_evidence.append(f"Hidden/White Text + System Instruction Override (+{boost} Risk)")

        if has_white_hidden and has_exfil:
            boost = self.config.correlation_boosts.get("data_exfil_plus_hidden", 25)
            correlation_boost += boost
            correlated_evidence.append(f"Hidden/White Text + Data Exfiltration Command (+{boost} Risk)")

        if has_obfuscation and (has_override or has_ats or has_exfil):
            boost = self.config.correlation_boosts.get("obfuscation_plus_injection", 15)
            correlation_boost += boost
            correlated_evidence.append(f"Obfuscated Text Structure + Active Prompt Injection (+{boost} Risk)")

        # 3. Calculate Final Risk Score (Capped between 0 and 100)
        final_score = min(100, raw_score + correlation_boost)

        # 4. Determine Verdict
        if final_score <= self.config.verdict_safe_max:
            verdict = Verdict.SAFE
        elif final_score <= self.config.verdict_suspicious_max:
            verdict = Verdict.SUSPICIOUS
        else:
            verdict = Verdict.HIGH_RISK

        # 5. Primary Threat Signal & Explainable Confidence Model
        max_finding_conf = max(f.confidence for f in findings)
        overall_confidence = min(1.0, round(max_finding_conf + (0.05 if correlation_boost > 0 else 0.0), 2))

        # Sort findings by severity
        sorted_findings = sorted(findings, key=lambda f: f.severity.value if hasattr(f.severity, "value") else str(f.severity), reverse=True)
        primary_threat = sorted_findings[0].category.value if sorted_findings else None

        # Build Verdict Explanation
        if verdict == Verdict.SAFE:
            explanation = f"SAFE: Low cumulative risk score ({final_score}/100) below threshold ({self.config.verdict_safe_max})."
        elif verdict == Verdict.SUSPICIOUS:
            explanation = f"SUSPICIOUS: Document contains suspicious layout or prompt indicators (Primary: {primary_threat}, Score: {final_score}/100)."
        else:
            explanation = f"HIGH RISK: Document contains severe security threat signals (Primary: {primary_threat})."

        if correlated_evidence:
            explanation += f" Correlated attacks detected: {'; '.join(correlated_evidence)}."

        # 6. Build Stage 4 Advanced Evidence, Attack Chains, and Top Contributing Evidence
        from securoxi.evidence import EvidenceAggregator
        aggregator = EvidenceAggregator(category_weights=self.config.category_weights)
        evidence_items_objs = aggregator.build_evidence_items(sorted_findings)
        attack_chains_objs = aggregator.synthesize_attack_chains(evidence_items_objs)
        top_contributing_objs = aggregator.get_top_contributing_evidence(evidence_items_objs, limit=3)

        return AnalysisReport(
            filename=filename,
            document_type=doc_type,
            verdict=verdict,
            risk_score=final_score,
            primary_threat=primary_threat,
            overall_confidence=overall_confidence,
            verdict_explanation=explanation,
            findings=sorted_findings,
            correlated_evidence=correlated_evidence,
            attack_chains=[c.to_dict() for c in attack_chains_objs],
            evidence_items=[e.to_dict() for e in evidence_items_objs],
            top_contributing_evidence=[t.to_dict() for t in top_contributing_objs],
            total_spans_analyzed=total_spans,
            execution_time_ms=execution_time_ms
        )

