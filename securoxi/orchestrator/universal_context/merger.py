"""
SECUROXI AI Intelligence 2.0 — Universal Context Merger & Validator (Phase 4 Stage 17)
Safely merges multi-source inputs (Files, Folders, JDs, ATS, Collections, Previous Tasks)
into one coherent, deduplicated, relational UniversalTaskContext with strict tenant isolation.
"""

from typing import Dict, Any, List, Optional
import time

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
    UniversalTaskContext,
)
from securoxi.orchestrator.universal_context.adapters import (
    FileInputAdapter,
    FolderInputAdapter,
    JDInputAdapter,
    ATSInputAdapter,
    CollectionInputAdapter,
    PreviousTaskAdapter,
)
from securoxi.logger import get_logger

logger = get_logger("orchestrator.universal_context")


class UniversalContextMerger:
    """
    Combines diverse raw inputs into a validated UniversalTaskContext:
    1. Dispatches to typed InputAdapters.
    2. Enforces tenant boundaries strictly.
    3. Deduplicates items with content hash preservation.
    4. Establishes relational graph between items (APPLIES_TO, CONTAINS).
    5. Ingests user constraints and source restrictions.
    """

    def __init__(self):
        self.file_adapter = FileInputAdapter()
        self.folder_adapter = FolderInputAdapter()
        self.jd_adapter = JDInputAdapter()
        self.ats_adapter = ATSInputAdapter()
        self.collection_adapter = CollectionInputAdapter()
        self.prev_task_adapter = PreviousTaskAdapter()

    def merge_inputs(
        self,
        raw_context: Optional[Dict[str, Any]],
        task_id: str,
        tenant_id: str,
        actor_id: str = "SYSTEM",
        constraints: Optional[List[str]] = None,
        source_restrictions: Optional[List[str]] = None,
    ) -> UniversalTaskContext:
        """Assembles and validates a UniversalTaskContext from heterogeneous sources."""
        ctx = UniversalTaskContext(
            task_id=task_id,
            tenant_id=tenant_id,
            actor_id=actor_id,
            source_restrictions=source_restrictions or [],
        )

        if not raw_context:
            return ctx

        # 1. Adapt Files
        if "files" in raw_context and raw_context["files"]:
            file_items = self.file_adapter.resolve(raw_context["files"], tenant_id)
            for item in file_items:
                ctx.add_item(item)

        # 2. Adapt Folder
        folder_item: Optional[ContextItem] = None
        if "folder" in raw_context and raw_context["folder"]:
            folder_items = self.folder_adapter.resolve(raw_context["folder"], tenant_id)
            if folder_items:
                folder_item = ctx.add_item(folder_items[0])

        # 3. Adapt Job Description
        jd_item: Optional[ContextItem] = None
        if "jobDescription" in raw_context and raw_context["jobDescription"]:
            jd_items = self.jd_adapter.resolve(raw_context["jobDescription"], tenant_id)
            if jd_items:
                jd_item = ctx.add_item(jd_items[0])
        elif "jd" in raw_context and raw_context["jd"]:
            jd_items = self.jd_adapter.resolve(raw_context["jd"], tenant_id)
            if jd_items:
                jd_item = ctx.add_item(jd_items[0])

        # 4. Adapt ATS Connection
        if "atsConnection" in raw_context and raw_context["atsConnection"]:
            ats_items = self.ats_adapter.resolve(raw_context["atsConnection"], tenant_id)
            for item in ats_items:
                ctx.add_item(item)

        # 5. Adapt Collection
        if "collection" in raw_context and raw_context["collection"]:
            col_items = self.collection_adapter.resolve(raw_context["collection"], tenant_id)
            for item in col_items:
                ctx.add_item(item)

        # 6. Adapt Previous Task Result
        if "previous_task_id" in raw_context or "previous_result" in raw_context:
            prev_input = raw_context.get("previous_result") or {"task_id": raw_context.get("previous_task_id")}
            prev_items = self.prev_task_adapter.resolve(prev_input, tenant_id)
            for item in prev_items:
                ctx.add_item(item)

        # 7. Establish Machine-Readable Relationships
        # JD -> Applies To Documents / Folder
        if jd_item:
            for item in ctx.items.values():
                if item.item_type in [ContextItemType.DOCUMENT, ContextItemType.CANDIDATE, ContextItemType.ATS_CANDIDATE]:
                    ctx.add_relationship(jd_item.context_item_id, item.context_item_id, RelationshipType.APPLIES_TO)
            if folder_item:
                ctx.add_relationship(jd_item.context_item_id, folder_item.context_item_id, RelationshipType.APPLIES_TO)

        # Folder -> Contains Documents
        if folder_item:
            for item in ctx.items.values():
                if item.item_type == ContextItemType.DOCUMENT and item.context_item_id != folder_item.context_item_id:
                    ctx.add_relationship(folder_item.context_item_id, item.context_item_id, RelationshipType.CONTAINS)

        # 8. User Constraints
        if constraints:
            for c_str in constraints:
                ctx.constraints.append(
                    ContextConstraint(
                        raw_text=c_str,
                        constraint_type="USER_SPECIFIED",
                        is_mandatory=True,
                    )
                )

        logger.info(f"UniversalTaskContext '{ctx.context_id}' assembled with {len(ctx.items)} items, {len(ctx.relationships)} relations (Tenant: {tenant_id})")
        return ctx
