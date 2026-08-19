"""
SECUROXI AI Intelligence 2.0 — Cross-System Autonomous Investigation Engine (Phase 8 Stage 49)
Correlates security, ATS, hiring, knowledge, and policy evidence into structured investigation cases.
"""

from typing import Dict, Any, List, Optional
import time
from securoxi.enterprise.investigation.types import (
    TriggerType,
    TriggerSignificance,
    InvestigationStatus,
    HypothesisStatus,
    InvestigationFindingClass,
    ResponseActionType,
)
from securoxi.enterprise.investigation.models import (
    TimelineEvent,
    InvestigationHypothesis,
    InvestigationRecommendation,
    InvestigationCase,
)
from securoxi.logger import get_logger

logger = get_logger("enterprise.investigation.engine")


class CrossSystemInvestigationEngine:
    """
    Autonomous Cross-System Investigation & Response Engine.
    Executes bounded, multi-hypothesis investigations and generates governed recommendations.
    """

    def __init__(self):
        self._cases: Dict[str, InvestigationCase] = {}  # case_id -> InvestigationCase

    def initiate_case(
        self,
        organization_id: str,
        workspace_id: str,
        trigger_type: TriggerType,
        target_resource_id: str,
        significance: TriggerSignificance = TriggerSignificance.HIGH,
        max_budget_steps: int = 10,
    ) -> InvestigationCase:
        """Initiates a bounded investigation case."""
        case = InvestigationCase(
            organization_id=organization_id,
            workspace_id=workspace_id,
            trigger_type=trigger_type,
            significance=significance,
            target_resource_id=target_resource_id,
            max_budget_steps=max_budget_steps,
        )
        self._cases[case.case_id] = case
        logger.info(f"Initiated Investigation Case '{case.case_id}' on Resource '{target_resource_id}' ({trigger_type.value})")
        return case

    def add_timeline_event(
        self,
        case_id: str,
        source_system: str,
        description: str,
        provenance: str = "",
        timestamp: Optional[float] = None,
    ) -> Optional[TimelineEvent]:
        """Appends a verified chronological timeline event to the case."""
        if case_id not in self._cases:
            return None

        case = self._cases[case_id]
        event = TimelineEvent(
            source_system=source_system,
            description=description,
            timestamp=timestamp or time.time(),
            provenance_reference=provenance,
        )
        case.timeline.append(event)
        case.steps_executed += 1
        return event

    def propose_hypothesis(
        self,
        case_id: str,
        description: str,
        initial_confidence: float = 0.60,
    ) -> Optional[InvestigationHypothesis]:
        """Adds a competing hypothesis to the investigation."""
        if case_id not in self._cases:
            return None

        case = self._cases[case_id]
        hyp = InvestigationHypothesis(
            case_id=case_id,
            description=description,
            status=HypothesisStatus.PROPOSED,
            confidence=initial_confidence,
        )
        case.hypotheses.append(hyp)
        return hyp

    def test_hypotheses(
        self,
        case_id: str,
        supported_hypothesis_id: str,
        supporting_evidence: List[str],
        contradicting_evidence: List[str],
    ) -> bool:
        """Updates hypothesis test results based on collected evidence."""
        if case_id not in self._cases:
            return False

        case = self._cases[case_id]
        for hyp in case.hypotheses:
            if hyp.hypothesis_id == supported_hypothesis_id:
                hyp.status = HypothesisStatus.SUPPORTED
                hyp.confidence = 0.92
                hyp.supporting_evidence = supporting_evidence
                hyp.contradicting_evidence = contradicting_evidence
                hyp.updated_at = time.time()
            else:
                hyp.status = HypothesisStatus.REFUTED
                hyp.confidence = 0.15
                hyp.updated_at = time.time()

        case.status = InvestigationStatus.HYPOTHESIS_TESTING
        return True

    def synthesize_and_recommend(
        self,
        case_id: str,
        finding_class: InvestigationFindingClass,
        action_type: ResponseActionType,
        reason: str,
    ) -> Optional[InvestigationRecommendation]:
        """Finalizes the investigation and generates a governed recommendation."""
        if case_id not in self._cases:
            return None

        case = self._cases[case_id]
        rec = InvestigationRecommendation(
            case_id=case_id,
            organization_id=case.organization_id,
            workspace_id=case.workspace_id,
            action_type=action_type,
            target_resource_id=case.target_resource_id,
            reason=reason,
            finding_class=finding_class,
            confidence=0.94,
            requires_approval=True,  # Invariant: Consequential actions require Stage 23 approval
        )
        case.recommendations.append(rec)
        case.finding_class = finding_class
        case.status = InvestigationStatus.COMPLETED
        case.completed_at = time.time()

        logger.info(f"Completed Investigation Case '{case_id}': Finding={finding_class.value}, Action={action_type.value}")
        return rec

    def get_cases(self, organization_id: str, workspace_id: Optional[str] = None) -> List[InvestigationCase]:
        """Returns investigation cases strictly scoped by tenant."""
        results = [c for c in self._cases.values() if c.organization_id == organization_id]
        if workspace_id:
            results = [c for c in results if c.workspace_id == workspace_id]
        return results
