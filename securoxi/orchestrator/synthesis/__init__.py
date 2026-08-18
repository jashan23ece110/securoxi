"""
SECUROXI AI Intelligence 2.0 — Cross-Document Research Synthesis Package
Exports ResearchSynthesizer, models, and types.
"""

from securoxi.orchestrator.synthesis.types import (
    SynthesisMode,
    ComparisonDimension,
    SynthesisStatus,
)
from securoxi.orchestrator.synthesis.models import (
    DerivedClaim,
    ComparisonItem,
    SynthesisResult,
)
from securoxi.orchestrator.synthesis.synthesizer import ResearchSynthesizer

__all__ = [
    "SynthesisMode",
    "ComparisonDimension",
    "SynthesisStatus",
    "DerivedClaim",
    "ComparisonItem",
    "SynthesisResult",
    "ResearchSynthesizer",
]
