"""
SECUROXI AI Intelligence 2.0 — Universal Input & Context Package (Phase 4 Stage 17)
Exports UniversalTaskContext, ContextItem, Adapters, Merger, and Manager.
"""

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
from securoxi.orchestrator.universal_context.adapters import (
    InputAdapter,
    FileInputAdapter,
    FolderInputAdapter,
    JDInputAdapter,
    ATSInputAdapter,
    CollectionInputAdapter,
    PreviousTaskAdapter,
)
from securoxi.orchestrator.universal_context.merger import UniversalContextMerger
from securoxi.orchestrator.universal_context.manager import UniversalContextManager

__all__ = [
    "ContextItemType",
    "ContextSourceType",
    "ContextScope",
    "ContextSecurityState",
    "ContextTrustLevel",
    "RelationshipType",
    "ContextStatus",
    "ContextItem",
    "ContextRelationship",
    "ContextConstraint",
    "ContextSnapshot",
    "UniversalTaskContext",
    "InputAdapter",
    "FileInputAdapter",
    "FolderInputAdapter",
    "JDInputAdapter",
    "ATSInputAdapter",
    "CollectionInputAdapter",
    "PreviousTaskAdapter",
    "UniversalContextMerger",
    "UniversalContextManager",
]
