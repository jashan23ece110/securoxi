"""
SECUROXI AI Intelligence 2.0 — Universal Context Manager (Phase 4 Stage 17)
Lifecycle management, validation, snapshotting, and querying of UniversalTaskContext instances.
"""

from typing import Dict, Any, List, Optional
import time
import threading

from securoxi.orchestrator.universal_context.types import (
    ContextItemType,
    ContextSourceType,
    ContextScope,
    ContextSecurityState,
    ContextTrustLevel,
    RelationshipType,
    ContextStatus,
)
from securoxi.orchestrator.universal_context.models import (
    ContextItem,
    ContextRelationship,
    ContextConstraint,
    ContextSnapshot,
    UniversalTaskContext,
)
from securoxi.orchestrator.universal_context.merger import UniversalContextMerger
from securoxi.logger import get_logger

logger = get_logger("orchestrator.universal_context")


class UniversalContextManager:
    """Thread-safe lifecycle manager for active and frozen UniversalTaskContexts."""

    def __init__(self, merger: Optional[UniversalContextMerger] = None):
        self.merger = merger or UniversalContextMerger()
        self._contexts: Dict[str, UniversalTaskContext] = {}
        self._lock = threading.Lock()

    def create_context(
        self,
        task_id: str,
        tenant_id: str,
        raw_inputs: Optional[Dict[str, Any]] = None,
        actor_id: str = "SYSTEM",
        constraints: Optional[List[str]] = None,
        source_restrictions: Optional[List[str]] = None,
    ) -> UniversalTaskContext:
        """Assembles, validates, and stores a new UniversalTaskContext."""
        ctx = self.merger.merge_inputs(
            raw_context=raw_inputs,
            task_id=task_id,
            tenant_id=tenant_id,
            actor_id=actor_id,
            constraints=constraints,
            source_restrictions=source_restrictions,
        )

        with self._lock:
            self._contexts[ctx.context_id] = ctx

        logger.info(f"Created UniversalTaskContext '{ctx.context_id}' for task '{task_id}' (Tenant: {tenant_id})")
        return ctx

    def get_context(self, context_id: str, tenant_id: str) -> Optional[UniversalTaskContext]:
        """Retrieves context ensuring tenant isolation."""
        with self._lock:
            ctx = self._contexts.get(context_id)
            if ctx and ctx.tenant_id == tenant_id:
                return ctx
            return None

    def validate_context(self, context: UniversalTaskContext) -> Dict[str, Any]:
        """Performs pre-flight validation on context safety, tenant isolation, and completeness."""
        issues: List[str] = []
        is_valid = True

        for item in context.items.values():
            if item.tenant_id != context.tenant_id:
                issues.append(f"Security violation: Item '{item.context_item_id}' tenant '{item.tenant_id}' mismatches context tenant '{context.tenant_id}'")
                is_valid = False

            if item.security_state == ContextSecurityState.HIGH_RISK and item.trust_level == ContextTrustLevel.TRUSTED_CONTEXT:
                issues.append(f"Trust violation: HIGH_RISK item '{item.title}' cannot be in TRUSTED_CONTEXT")
                is_valid = False

            if item.security_state == ContextSecurityState.UNINSPECTABLE and item.trust_level == ContextTrustLevel.TRUSTED_CONTEXT:
                issues.append(f"Trust violation: UNINSPECTABLE item '{item.title}' cannot be in TRUSTED_CONTEXT")
                is_valid = False

        return {
            "is_valid": is_valid,
            "items_count": len(context.items),
            "relationships_count": len(context.relationships),
            "issues": issues,
            "status": "VALID" if is_valid else "INVALID",
        }

    def freeze_context(self, context_id: str, tenant_id: str) -> Optional[ContextSnapshot]:
        """Freezes context and creates reproducible snapshot."""
        with self._lock:
            ctx = self._contexts.get(context_id)
            if not ctx or ctx.tenant_id != tenant_id:
                return None
            return ctx.freeze()

    def list_contexts(self, tenant_id: str, limit: int = 50) -> List[UniversalTaskContext]:
        """Lists active contexts for tenant."""
        with self._lock:
            return [
                c for c in self._contexts.values()
                if c.tenant_id == tenant_id
            ][:limit]
