"""
SECUROXI AI Intelligence 2.0 — Controlled Adaptive Improvement Engine
Orchestrates production feedback ingestion, triage, validation, clustering,
improvement candidate generation, Stage 33 continuous evaluation, and human governance.
Strictly prohibits autonomous production self-modification.
"""

from typing import Dict, Any, List, Optional
import time
from securoxi.orchestrator.feedback.types import (
    FeedbackCategory,
    FeedbackSource,
    FeedbackValidationState,
    FeedbackSeverity,
    ImprovementStatus,
)
from securoxi.orchestrator.feedback.models import (
    FeedbackEvent,
    FeedbackCluster,
    ImprovementCandidate,
)
from securoxi.orchestrator.evaluation.engine import ContinuousEvaluationEngine
from securoxi.orchestrator.evaluation.types import EvaluationLevel, GateStatus
from securoxi.logger import get_logger

logger = get_logger("orchestrator.feedback")


class ControlledAdaptiveImprovementEngine:
    """
    Controlled Adaptive Improvement Pipeline.
    Converts production telemetry and validated user feedback into verified,
    versioned, human-governed engineering improvements.
    """

    def __init__(self, evaluation_engine: Optional[ContinuousEvaluationEngine] = None):
        self.eval_engine = evaluation_engine or ContinuousEvaluationEngine()
        self._feedback_events: Dict[str, FeedbackEvent] = {}
        self._clusters: Dict[str, FeedbackCluster] = {}
        self._candidates: Dict[str, ImprovementCandidate] = {}

    def record_feedback(self, event: FeedbackEvent) -> str:
        """Records an incoming feedback signal from users, recruiters, or security analysts."""
        self._feedback_events[event.feedback_id] = event
        logger.info(f"Recorded feedback '{event.feedback_id}' from {event.source.value} (Category: {event.category.value})")
        return event.feedback_id

    def triage_and_validate(
        self,
        feedback_id: str,
        is_valid: bool,
        notes: str = "",
        severity: Optional[FeedbackSeverity] = None,
    ) -> bool:
        """
        Validates or rejects a feedback event.
        Requires analyst/human validation before becoming an improvement signal.
        """
        if feedback_id not in self._feedback_events:
            return False

        event = self._feedback_events[feedback_id]
        if is_valid:
            event.validation_state = FeedbackValidationState.VALIDATED
            if severity:
                event.severity = severity
        else:
            event.validation_state = FeedbackValidationState.REJECTED

        event.validation_notes = notes
        return True

    def cluster_feedback(self, tenant_id: Optional[str] = None) -> List[FeedbackCluster]:
        """Groups validated feedback events by category and component to identify themes."""
        groups: Dict[str, List[FeedbackEvent]] = {}
        for event in self._feedback_events.values():
            if event.validation_state != FeedbackValidationState.VALIDATED:
                continue
            if tenant_id and event.tenant_id != tenant_id:
                continue

            key = f"{event.category.value}:{event.affected_component}"
            if key not in groups:
                groups[key] = []
            groups[key].append(event)

        clusters = []
        for key, events in groups.items():
            cat = events[0].category
            comp = events[0].affected_component
            max_sev = max(events, key=lambda e: 3 if e.severity == FeedbackSeverity.CRITICAL else (2 if e.severity == FeedbackSeverity.HIGH else 1)).severity
            cluster = FeedbackCluster(
                category=cat,
                affected_component=comp,
                feedback_ids=[e.feedback_id for e in events],
                frequency=len(events),
                root_cause_summary=f"{len(events)} reports on {comp} ({cat.value})",
                severity=max_sev,
            )
            self._clusters[cluster.cluster_id] = cluster
            clusters.append(cluster)

        return clusters

    def create_improvement_candidate(
        self,
        cluster_id: str,
        proposed_change: str,
        expected_benefit: str,
    ) -> Optional[ImprovementCandidate]:
        """Creates a formal ImprovementCandidate from a validated feedback cluster."""
        if cluster_id not in self._clusters:
            return None

        cluster = self._clusters[cluster_id]
        candidate = ImprovementCandidate(
            cluster_id=cluster_id,
            affected_component=cluster.affected_component,
            problem_statement=cluster.root_cause_summary,
            proposed_change=proposed_change,
            expected_benefit=expected_benefit,
            status=ImprovementStatus.PROPOSED,
        )
        self._candidates[candidate.candidate_id] = candidate
        return candidate

    def evaluate_improvement(
        self,
        candidate_id: str,
        measured_metrics: Dict[str, float],
    ) -> bool:
        """Executes Stage 33 Continuous Evaluation against the proposed improvement."""
        if candidate_id not in self._candidates:
            return False

        candidate = self._candidates[candidate_id]
        candidate.status = ImprovementStatus.IN_EVALUATION

        eval_result = self.eval_engine.evaluate_run(
            measured_metrics=measured_metrics,
            level=EvaluationLevel.LEVEL_2_STANDARD,
            commit_sha=f"IMP-{candidate_id}",
        )
        candidate.evaluation_run_id = eval_result.run_id

        if eval_result.overall_status == GateStatus.PASS:
            candidate.status = ImprovementStatus.UNDER_REVIEW
            return True
        else:
            candidate.status = ImprovementStatus.REJECTED
            return False

    def approve_improvement(
        self,
        candidate_id: str,
        approver_id: str,
    ) -> bool:
        """Applies required human governance approval to a passing improvement candidate."""
        if candidate_id not in self._candidates:
            return False

        candidate = self._candidates[candidate_id]
        if candidate.status != ImprovementStatus.UNDER_REVIEW:
            logger.error(f"Candidate '{candidate_id}' cannot be approved in state '{candidate.status.value}'")
            return False

        candidate.approved_by = approver_id
        candidate.approval_timestamp = time.time()
        candidate.status = ImprovementStatus.APPROVED
        return True

    def canary_release(
        self,
        candidate_id: str,
        version: str,
    ) -> bool:
        """Promotes an approved improvement into a versioned canary deployment."""
        if candidate_id not in self._candidates:
            return False

        candidate = self._candidates[candidate_id]
        if candidate.status != ImprovementStatus.APPROVED:
            logger.error(f"Candidate '{candidate_id}' must be APPROVED before release")
            return False

        candidate.release_version = version
        candidate.status = ImprovementStatus.RELEASED
        return True
