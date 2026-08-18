"""
SECUROXI AI Intelligence 2.0 — Evidence Gap Engine
Analyzes accumulated retrieved chunks against formal evidence requirements,
identifying missing entities, context, and attributes to formulate targeted follow-up hops.
"""

from typing import Dict, Any, List, Optional
from securoxi.orchestrator.retrieval_execution.types import EvidenceGapType
from securoxi.orchestrator.retrieval_execution.models import EvidenceGap
from securoxi.orchestrator.retrieval_planner.models import EvidenceRequirement
from securoxi.logger import get_logger

logger = get_logger("orchestrator.evidence_gap_engine")


class EvidenceGapEngine:
    """Detects missing evidence attributes and drives targeted multi-hop query refinement."""

    def evaluate_gaps(
        self,
        accumulated_chunks: List[Dict[str, Any]],
        requirements: List[EvidenceRequirement],
        original_objective: str,
    ) -> List[EvidenceGap]:
        """
        Evaluates accumulated chunks against formal requirements:
        1. Checks topic coverage.
        2. Identifies missing context (e.g., 'production' environment or 'security' hardening).
        3. Formulates targeted follow-up query suggestions.
        """
        gaps: List[EvidenceGap] = []
        combined_text = " ".join([c.get("content", c.get("text", "")).lower() for c in accumulated_chunks])

        for req in requirements:
            topic_lower = req.topic.lower()
            if topic_lower not in combined_text:
                # Missing entire topic/entity
                gaps.append(
                    EvidenceGap(
                        gap_type=EvidenceGapType.MISSING_ENTITY,
                        target_topic=req.topic,
                        description=f"Evidence for required topic '{req.topic}' not yet found in accumulated chunks.",
                        required_terms=[req.topic],
                        suggested_query=f"{req.topic} documentation experience",
                    )
                )
            else:
                # Check for context requirements if specified in objective
                if "production" in original_objective.lower() and "production" not in combined_text:
                    gaps.append(
                        EvidenceGap(
                            gap_type=EvidenceGapType.MISSING_CONTEXT,
                            target_topic=req.topic,
                            description=f"Topic '{req.topic}' found, but production environment context is missing.",
                            required_terms=[req.topic, "production"],
                            suggested_query=f"production {req.topic} cluster deployment management",
                        )
                    )

        return gaps
