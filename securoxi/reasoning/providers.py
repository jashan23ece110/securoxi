"""
SECUROXI AI Reasoning Providers
Includes RuleBasedMockReasoningProvider (offline/test fallback) and
GeminiReasoningProvider (replaceable Gemini API provider).
"""

import os
import json
import re
from typing import List, Dict, Any, Optional
from securoxi.logger import get_logger
from securoxi.models import SecurityFinding, AttackCategory
from securoxi.reasoning.base import BaseReasoningProvider, ReasoningResult, AttackIntent
from securoxi.reasoning.prompt import build_security_analysis_prompt


class RuleBasedMockReasoningProvider(BaseReasoningProvider):
    """
    Deterministic rule-assisted mock reasoning provider for offline testing and fallback evaluation.
    Provides explainable intent classification without external API calls.
    """

    def __init__(self, name: str = "RuleBasedMockProvider"):
        self.name = name
        self.logger = get_logger("securoxi.reasoning.mock")

    def evaluate_findings(
        self,
        findings: List[SecurityFinding],
        document_text_context: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ReasoningResult:
        if not findings:
            return ReasoningResult(
                attack_intent=AttackIntent.LEGITIMATE_CONTEXT,
                reasoning_summary="No security findings present. Context is legitimate.",
                confidence=1.0,
                supporting_evidence=[],
                is_prompt_injection_attempt=False,
                is_visual_deception_attempt=False,
                provider_name=self.name
            )

        categories = {f.category for f in findings}
        evidence_list = [f.evidence for f in findings if f.evidence]

        has_injection_cat = any(cat in categories for cat in [
            AttackCategory.INSTRUCTION_OVERRIDE,
            AttackCategory.SYSTEM_PROMPT_MANIPULATION,
            AttackCategory.ATS_MANIPULATION,
            AttackCategory.AI_ROLE_MANIPULATION,
            AttackCategory.DATA_EXFILTRATION,
            AttackCategory.TOOL_MANIPULATION
        ])

        has_visual_cat = any(cat in categories for cat in [
            AttackCategory.MICRO_TEXT,
            AttackCategory.WHITE_TEXT,
            AttackCategory.BACKGROUND_MATCH,
            AttackCategory.HIDDEN_TEXT,
            AttackCategory.INVISIBLE_UNICODE,
            AttackCategory.SUSPICIOUS_POSITION
        ])

        # Check for legitimate header/graphic formatting (e.g. EMMA WATSON - SENIOR UX DESIGNER white text)
        is_legitimate_graphic_header = (
            AttackCategory.WHITE_TEXT in categories and 
            not has_injection_cat and
            not bool(re.search(r"\b(ignore|disregard|system prompt|rate candidate|rank 10/10|10/10|unconditionally|jailbreak)\b", document_text_context.lower()))
        )


        if is_legitimate_graphic_header:
            return ReasoningResult(
                attack_intent=AttackIntent.BENIGN_FORMATTING,
                reasoning_summary="White text is used legitimately over dark header graphics banner for UX design title.",
                confidence=0.92,
                supporting_evidence=evidence_list[:1],
                is_prompt_injection_attempt=False,
                is_visual_deception_attempt=False,
                provider_name=self.name
            )

        if has_injection_cat and has_visual_cat:
            return ReasoningResult(
                attack_intent=AttackIntent.GENUINE_ATTACK,
                reasoning_summary="Correlated attack: Visually concealed text contains explicit prompt injection or candidate rating manipulation.",
                confidence=0.98,
                supporting_evidence=evidence_list[:2],
                is_prompt_injection_attempt=True,
                is_visual_deception_attempt=True,
                provider_name=self.name
            )

        if has_injection_cat:
            return ReasoningResult(
                attack_intent=AttackIntent.GENUINE_ATTACK,
                reasoning_summary="Document text contains explicit prompt injection or instruction override directive.",
                confidence=0.95,
                supporting_evidence=evidence_list[:2],
                is_prompt_injection_attempt=True,
                is_visual_deception_attempt=False,
                provider_name=self.name
            )

        if has_visual_cat:
            return ReasoningResult(
                attack_intent=AttackIntent.AMBIGUOUS_SUSPICIOUS,
                reasoning_summary="Document contains visually hidden text or micro-formatting without explicit prompt injection keywords.",
                confidence=0.85,
                supporting_evidence=evidence_list[:2],
                is_prompt_injection_attempt=False,
                is_visual_deception_attempt=True,
                provider_name=self.name
            )

        return ReasoningResult(
            attack_intent=AttackIntent.LEGITIMATE_CONTEXT,
            reasoning_summary="Content analyzed and determined to be legitimate.",
            confidence=0.90,
            supporting_evidence=[],
            is_prompt_injection_attempt=False,
            is_visual_deception_attempt=False,
            provider_name=self.name
        )


class GeminiReasoningProvider(BaseReasoningProvider):
    """
    Replaceable Gemini API reasoning provider.
    Executes security analysis prompts inside strict XML tag isolation using Gemini models.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.logger = get_logger("securoxi.reasoning.gemini")

    def evaluate_findings(
        self,
        findings: List[SecurityFinding],
        document_text_context: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ReasoningResult:
        if not self.api_key:
            self.logger.warning("No API key available for GeminiReasoningProvider. Falling back to RuleBasedMockReasoningProvider.")
            fallback = RuleBasedMockReasoningProvider()
            return fallback.evaluate_findings(findings, document_text_context, metadata)

        prompt = build_security_analysis_prompt(findings, document_text_context)

        try:
            # Import google-genai dynamically if installed
            import google.genai as genai
            client = genai.Client(api_key=self.api_key)

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            response_text = response.text if hasattr(response, "text") else str(response)
            
            # Extract JSON payload from model response
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if not json_match:
                raise ValueError("Model output did not contain valid JSON payload.")

            data = json.loads(json_match.group(0))

            intent_str = data.get("attack_intent", "AMBIGUOUS_SUSPICIOUS")
            try:
                intent = AttackIntent(intent_str)
            except ValueError:
                intent = AttackIntent.AMBIGUOUS_SUSPICIOUS

            return ReasoningResult(
                attack_intent=intent,
                reasoning_summary=str(data.get("reasoning_summary", "Analysis completed.")),
                confidence=float(data.get("confidence", 0.90)),
                supporting_evidence=list(data.get("supporting_evidence", [])),
                is_prompt_injection_attempt=bool(data.get("is_prompt_injection_attempt", False)),
                is_visual_deception_attempt=bool(data.get("is_visual_deception_attempt", False)),
                provider_name=f"GeminiReasoningProvider({self.model_name})"
            )

        except Exception as e:
            self.logger.error(f"GeminiReasoningProvider API error: {str(e)}. Falling back to RuleBasedMockReasoningProvider.")
            fallback = RuleBasedMockReasoningProvider()
            return fallback.evaluate_findings(findings, document_text_context, metadata)
