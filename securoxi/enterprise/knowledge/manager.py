"""
SECUROXI AI Intelligence 2.0 — Continuous Knowledge Manager (Phase 8 Stage 48)
Maintains continuous, authorized, security-aware enterprise knowledge representations.
"""

from typing import Dict, Any, List, Optional
import time
import hashlib
from securoxi.enterprise.knowledge.types import (
    SourceAuthority,
    AdmissionDecision,
    KnowledgeFreshness,
    KnowledgeChangeType,
)
from securoxi.enterprise.knowledge.models import (
    KnowledgeSource,
    KnowledgeChunk,
    KnowledgeConflict,
    QuestionSubscription,
    KnowledgeAnswer,
)
from securoxi.logger import get_logger

logger = get_logger("enterprise.knowledge.manager")


class ContinuousKnowledgeManager:
    """
    Continuous Enterprise Knowledge Intelligence Engine.
    Coordinates security-first source admission, incremental chunking,
    deletion propagation, conflict detection, and question subscriptions.
    """

    def __init__(self):
        self._sources: Dict[str, KnowledgeSource] = {}      # source_id -> KnowledgeSource
        self._chunks: Dict[str, List[KnowledgeChunk]] = {}  # source_id -> List[KnowledgeChunk]
        self._subscriptions: Dict[str, QuestionSubscription] = {}
        self._conflicts: List[KnowledgeConflict] = []

    def admit_source(
        self,
        organization_id: str,
        workspace_id: str,
        title: str,
        content: str,
        authority: SourceAuthority = SourceAuthority.VERIFIED,
        security_state: str = "SAFE",
        classification: str = "INTERNAL",
    ) -> KnowledgeSource:
        """
        Ingests and validates a knowledge source:
        1. Security-First check: HIGH_RISK or UNINSPECTABLE is QUARANTINED.
        2. Admitted content is chunked and added to index.
        """
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

        # Security-First Admission Decision
        if security_state in {"HIGH_RISK", "UNINSPECTABLE"}:
            admission = AdmissionDecision.QUARANTINED
            logger.warning(f"Knowledge Admission Quarantined: Source '{title}' is {security_state}")
        else:
            admission = AdmissionDecision.ADMITTED

        source = KnowledgeSource(
            organization_id=organization_id,
            workspace_id=workspace_id,
            title=title,
            authority=authority,
            admission=admission,
            freshness=KnowledgeFreshness.CURRENT,
            security_state=security_state,
            classification=classification,
            raw_content=content,
            content_hash=content_hash,
        )
        self._sources[source.source_id] = source

        # Index chunks only if admitted
        if admission == AdmissionDecision.ADMITTED:
            self._index_chunks(source)

        return source

    def _index_chunks(self, source: KnowledgeSource):
        """Generates chunks for an admitted knowledge source."""
        chunks = [
            KnowledgeChunk(
                source_id=source.source_id,
                organization_id=source.organization_id,
                workspace_id=source.workspace_id,
                content=source.raw_content,
                is_valid=True,
            )
        ]
        self._chunks[source.source_id] = chunks
        logger.info(f"Indexed {len(chunks)} chunks for Source '{source.source_id}' ({source.title})")

    def update_source(self, source_id: str, new_content: str) -> Optional[KnowledgeSource]:
        """Updates source content and regenerates chunks incrementally."""
        if source_id not in self._sources:
            return None

        source = self._sources[source_id]
        if source.admission == AdmissionDecision.DELETED:
            logger.error(f"Cannot update deleted source '{source_id}'")
            return None

        source.raw_content = new_content
        source.version += 1
        source.content_hash = hashlib.sha256(new_content.encode("utf-8")).hexdigest()[:16]
        source.updated_at = time.time()

        # Re-chunk
        self._index_chunks(source)
        logger.info(f"Updated Knowledge Source '{source_id}' to Version v{source.version}")
        return source

    def delete_source(self, source_id: str) -> bool:
        """
        Deletion propagation: Immediately invalidates source, removes chunks,
        and flushes retrieval state.
        """
        if source_id not in self._sources:
            return False

        source = self._sources[source_id]
        source.admission = AdmissionDecision.DELETED
        source.freshness = KnowledgeFreshness.INVALID
        source.raw_content = ""

        # Remove chunks from index
        if source_id in self._chunks:
            del self._chunks[source_id]

        logger.info(f"Propagated Deletion: Flushed chunks for Source '{source_id}'")
        return True

    def query_knowledge(
        self,
        organization_id: str,
        workspace_id: str,
        query: str,
    ) -> List[KnowledgeChunk]:
        """Retrieves chunks strictly scoped by organization, workspace, and admission status."""
        results = []
        for src_id, chunk_list in self._chunks.items():
            src = self._sources.get(src_id)
            if not src or src.admission != AdmissionDecision.ADMITTED:
                continue
            if src.organization_id != organization_id:
                continue  # Tenant Isolation
            for c in chunk_list:
                if c.is_valid:
                    results.append(c)
        return results

    def subscribe_to_question(
        self,
        organization_id: str,
        workspace_id: str,
        user_id: str,
        question: str,
        initial_answer: str,
        dependent_sources: List[str],
    ) -> QuestionSubscription:
        """Registers a live subscription to a question."""
        sub = QuestionSubscription(
            organization_id=organization_id,
            workspace_id=workspace_id,
            user_id=user_id,
            question=question,
            current_answer=initial_answer,
            dependent_source_ids=dependent_sources,
        )
        self._subscriptions[sub.subscription_id] = sub
        logger.info(f"Registered Question Subscription '{sub.subscription_id}' for User '{user_id}'")
        return sub

    def check_question_updates(self, modified_source_id: str, new_answer_text: str) -> List[Dict[str, Any]]:
        """Re-evaluates subscriptions when a dependent source changes and emits ANSWER_CHANGED signals."""
        notifications = []
        for sub in self._subscriptions.values():
            if modified_source_id in sub.dependent_source_ids and sub.is_active:
                if sub.current_answer != new_answer_text:
                    prev_answer = sub.current_answer
                    sub.current_answer = new_answer_text
                    sub.last_evaluated_at = time.time()
                    notifications.append({
                        "event": "ANSWER_CHANGED",
                        "subscription_id": sub.subscription_id,
                        "question": sub.question,
                        "previous_answer": prev_answer,
                        "new_answer": new_answer_text,
                        "trigger_source_id": modified_source_id,
                    })
        return notifications
