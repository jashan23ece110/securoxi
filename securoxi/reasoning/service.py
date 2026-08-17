"""
SECUROXI AI Reasoning Service Orchestrator
Orchestrates AI reasoning layer execution, provider selection, and report enrichment.
"""

from typing import List, Optional, Dict, Any
from securoxi.config import SecuroxiConfig
from securoxi.logger import get_logger
from securoxi.models import SecurityFinding, AnalysisReport, Verdict
from securoxi.reasoning.base import BaseReasoningProvider, ReasoningResult, AttackIntent
from securoxi.reasoning.providers import RuleBasedMockReasoningProvider, GeminiReasoningProvider


class SecuroxiReasoningService:
    """
    Top-level orchestrator for AI Security Reasoning Layer.
    Executes reasoning evaluation safely and enriches security reports.
    """

    def __init__(self, config: Optional[SecuroxiConfig] = None, provider: Optional[BaseReasoningProvider] = None):
        self.config = config or SecuroxiConfig()
        self.logger = get_logger("securoxi.reasoning.service")
        
        if provider:
            self.provider = provider
        else:
            provider_type = getattr(self.config, "ai_provider", "mock")
            if provider_type == "gemini":
                self.provider = GeminiReasoningProvider(model_name=getattr(self.config, "gemini_model", "gemini-2.5-flash"))
            else:
                self.provider = RuleBasedMockReasoningProvider()

    def reason(self, prompt: str) -> ReasoningResult:
        """Execute AI reasoning for a query prompt string."""
        return self.provider.evaluate_findings(
            findings=[],
            document_text_context=prompt,
            metadata={}
        )

    def evaluate_report(self, report: AnalysisReport, document_text_context: str = "") -> AnalysisReport:
        """
        Evaluate security report findings with AI reasoning layer if enabled.
        Does NOT blindly override deterministic findings.
        """
        if not getattr(self.config, "ai_reasoning_enabled", True):
            self.logger.info("AI Reasoning Layer is disabled in config. Skipping.")
            return report

        if not report.findings and report.verdict == Verdict.SAFE:
            # Document is completely clean deterministically; no AI evaluation needed
            return report

        try:
            self.logger.info(f"Executing AI Reasoning Layer ({self.provider.__class__.__name__}) for '{report.filename}'")
            reasoning_result: ReasoningResult = self.provider.evaluate_findings(
                findings=report.findings,
                document_text_context=document_text_context,
                metadata=report.metadata
            )

            # Store AI Reasoning Result in report metadata
            report.metadata["ai_reasoning"] = reasoning_result.to_dict()

            # Apply AI Reasoning Insights without overriding deterministic core
            if reasoning_result.attack_intent == AttackIntent.BENIGN_FORMATTING:
                # If AI reasoning certifies graphic formatting (e.g. white header banner text on dark bg rect)
                # and no prompt injection attacks exist, adjust score to SAFE
                has_injection = any(f.category for f in report.findings if f.category in [
                    "INSTRUCTION_OVERRIDE", "SYSTEM_PROMPT_MANIPULATION", "ATS_MANIPULATION", "DATA_EXFILTRATION", "TOOL_MANIPULATION"
                ])
                if not has_injection:
                    report.risk_score = 0
                    report.verdict = Verdict.SAFE
                    report.verdict_explanation += f" [AI Reasoning Note: {reasoning_result.reasoning_summary}]"
            elif reasoning_result.attack_intent == AttackIntent.GENUINE_ATTACK:
                # Reinforce attack verdict explanation
                report.verdict_explanation += f" [AI Security Audit: {reasoning_result.reasoning_summary}]"

        except Exception as e:
            self.logger.error(f"AI Reasoning Service execution failed: {str(e)}. Preserving deterministic findings.")
            report.metadata["ai_reasoning_error"] = str(e)

        return report
