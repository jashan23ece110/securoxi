"""
SECUROXI AI Modular Reasoning Layer Base Interface
Defines structured reasoning models, result data structures, and provider interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from securoxi.models import SecurityFinding


class AttackIntent(str, Enum):
    GENUINE_ATTACK = "GENUINE_ATTACK"              # Intentional prompt injection or deception
    LEGITIMATE_CONTEXT = "LEGITIMATE_CONTEXT"        # Legitimate corporate text or job title
    AMBIGUOUS_SUSPICIOUS = "AMBIGUOUS_SUSPICIOUS"    # Ambiguous content requiring human review
    BENIGN_FORMATTING = "BENIGN_FORMATTING"          # Legitimate graphic or layout formatting


@dataclass
class ReasoningResult:
    """Structured security intent analysis returned by AI reasoning provider."""
    attack_intent: AttackIntent
    reasoning_summary: str
    confidence: float                                # 0.0 to 1.0
    supporting_evidence: List[str] = field(default_factory=list)
    is_prompt_injection_attempt: bool = False
    is_visual_deception_attempt: bool = False
    provider_name: str = "MockProvider"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attack_intent": self.attack_intent.value,
            "reasoning_summary": self.reasoning_summary,
            "confidence": round(self.confidence, 2),
            "supporting_evidence": self.supporting_evidence,
            "is_prompt_injection_attempt": self.is_prompt_injection_attempt,
            "is_visual_deception_attempt": self.is_visual_deception_attempt,
            "provider_name": self.provider_name,
            "metadata": self.metadata
        }


class BaseReasoningProvider(ABC):
    """Abstract base class for AI security reasoning providers (Gemini, Mock, etc.)."""

    @abstractmethod
    def evaluate_findings(
        self,
        findings: List[SecurityFinding],
        document_text_context: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ReasoningResult:
        """
        Evaluate suspicious findings and document context for attack intent.
        Must execute inside an isolated security boundary.
        """
        pass
