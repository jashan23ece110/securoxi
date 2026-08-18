"""
SECUROXI AI Intelligence 2.0 — Universal Context Data Models (Phase 4 Stage 17)
Strongly typed data contracts for ContextItem, Relationships, Snapshots, and UniversalTaskContext.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time
import uuid
import hashlib

from securoxi.orchestrator.universal_context.types import (
    ContextItemType,
    ContextSourceType,
    ContextScope,
    ContextSecurityState,
    ContextTrustLevel,
    RelationshipType,
    ContextStatus,
)


@dataclass
class ContextRelationship:
    """Explicit, machine-readable link between two context items."""
    relationship_id: str = field(default_factory=lambda: f"REL-{uuid.uuid4().hex[:8].upper()}")
    source_item_id: str = ""
    target_item_id: str = ""
    relationship_type: RelationshipType = RelationshipType.REFERENCES
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relationship_id": self.relationship_id,
            "source_item_id": self.source_item_id,
            "target_item_id": self.target_item_id,
            "relationship_type": self.relationship_type.value,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


@dataclass
class ContextConstraint:
    """User-specified or system-enforced condition on how context is consumed."""
    constraint_id: str = field(default_factory=lambda: f"CST-{uuid.uuid4().hex[:8].upper()}")
    raw_text: str = ""
    constraint_type: str = "FILTER"
    is_mandatory: bool = True
    target_source: Optional[ContextSourceType] = None
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "constraint_id": self.constraint_id,
            "raw_text": self.raw_text,
            "constraint_type": self.constraint_type,
            "is_mandatory": self.is_mandatory,
            "target_source": self.target_source.value if self.target_source else None,
            "parameters": self.parameters,
        }


@dataclass
class ContextItem:
    """An individual structured context unit (file, folder, JD, ATS candidate, etc.)."""
    context_item_id: str = field(default_factory=lambda: f"CTX-{uuid.uuid4().hex[:10].upper()}")
    item_type: ContextItemType = ContextItemType.DOCUMENT
    source_type: ContextSourceType = ContextSourceType.LOCAL_UPLOAD
    source_id: str = ""
    tenant_id: str = "TENANT-DEFAULT"
    scope: ContextScope = ContextScope.DOCUMENT
    security_state: ContextSecurityState = ContextSecurityState.UNKNOWN
    trust_level: ContextTrustLevel = ContextTrustLevel.TRUSTED_CONTEXT
    title: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    content_hash: Optional[str] = None
    size_bytes: int = 0
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None

    def compute_hash(self, content_str: str) -> str:
        """Computes deterministic sha256 identifier for deduplication."""
        self.content_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()
        return self.content_hash

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_item_id": self.context_item_id,
            "item_type": self.item_type.value,
            "source_type": self.source_type.value,
            "source_id": self.source_id,
            "tenant_id": self.tenant_id,
            "scope": self.scope.value,
            "security_state": self.security_state.value,
            "trust_level": self.trust_level.value,
            "title": self.title,
            "metadata": self.metadata,
            "content_hash": self.content_hash,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }


@dataclass
class ContextSnapshot:
    """Immutable, point-in-time capture of context state for audit & reproducibility."""
    snapshot_id: str = field(default_factory=lambda: f"SNAP-{uuid.uuid4().hex[:10].upper()}")
    context_id: str = ""
    task_id: str = ""
    tenant_id: str = ""
    version: int = 1
    items_count: int = 0
    items_summary: Dict[str, int] = field(default_factory=dict)
    frozen_at: float = field(default_factory=time.time)
    serialized_items: List[Dict[str, Any]] = field(default_factory=list)
    serialized_relationships: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "context_id": self.context_id,
            "task_id": self.task_id,
            "tenant_id": self.tenant_id,
            "version": self.version,
            "items_count": self.items_count,
            "items_summary": self.items_summary,
            "frozen_at": self.frozen_at,
            "serialized_items": self.serialized_items,
            "serialized_relationships": self.serialized_relationships,
        }


@dataclass
class UniversalTaskContext:
    """
    Unified, structured context container uniting files, folders, JDs, ATS,
    collections, and user constraints with strict tenant isolation.
    """
    context_id: str = field(default_factory=lambda: f"UCTX-{uuid.uuid4().hex[:10].upper()}")
    task_id: str = "TASK-DEFAULT"
    tenant_id: str = "TENANT-DEFAULT"
    actor_id: str = "SYSTEM"
    version: int = 1
    status: ContextStatus = ContextStatus.ACTIVE
    items: Dict[str, ContextItem] = field(default_factory=dict)
    relationships: List[ContextRelationship] = field(default_factory=list)
    constraints: List[ContextConstraint] = field(default_factory=list)
    source_restrictions: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    snapshot: Optional[ContextSnapshot] = None

    def add_item(self, item: ContextItem) -> ContextItem:
        """Adds a validated item, ensuring tenant isolation."""
        if self.status == ContextStatus.FROZEN:
            raise RuntimeError(f"Cannot add item to FROZEN context '{self.context_id}'")
        if item.tenant_id != self.tenant_id:
            raise ValueError(f"Tenant mismatch: Context ({self.tenant_id}) vs Item ({item.tenant_id})")

        self.items[item.context_item_id] = item
        self.version += 1
        self.updated_at = time.time()
        return item

    def remove_item(self, item_id: str) -> Optional[ContextItem]:
        """Removes an item and any related relationships."""
        if self.status == ContextStatus.FROZEN:
            raise RuntimeError(f"Cannot remove item from FROZEN context '{self.context_id}'")

        item = self.items.pop(item_id, None)
        if item:
            self.relationships = [
                r for r in self.relationships
                if r.source_item_id != item_id and r.target_item_id != item_id
            ]
            self.version += 1
            self.updated_at = time.time()
        return item

    def get_item(self, item_id: str) -> Optional[ContextItem]:
        return self.items.get(item_id)

    def list_items(self, item_type: Optional[ContextItemType] = None) -> List[ContextItem]:
        if item_type is None:
            return list(self.items.values())
        return [i for i in self.items.values() if i.item_type == item_type]

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: RelationshipType,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ContextRelationship:
        """Creates machine-readable link between two items in this context."""
        rel = ContextRelationship(
            source_item_id=source_id,
            target_item_id=target_id,
            relationship_type=relationship_type,
            metadata=metadata or {},
        )
        self.relationships.append(rel)
        self.updated_at = time.time()
        return rel

    def get_related_items(
        self,
        item_id: str,
        relationship_type: Optional[RelationshipType] = None,
    ) -> List[ContextItem]:
        """Finds all items connected to item_id."""
        related_ids = []
        for r in self.relationships:
            if r.source_item_id == item_id:
                if relationship_type is None or r.relationship_type == relationship_type:
                    related_ids.append(r.target_item_id)
        return [self.items[rid] for rid in related_ids if rid in self.items]

    def freeze(self) -> ContextSnapshot:
        """Freezes context and creates an immutable snapshot."""
        summary: Dict[str, int] = {}
        for item in self.items.values():
            t_name = item.item_type.value
            summary[t_name] = summary.get(t_name, 0) + 1

        self.status = ContextStatus.FROZEN
        self.snapshot = ContextSnapshot(
            context_id=self.context_id,
            task_id=self.task_id,
            tenant_id=self.tenant_id,
            version=self.version,
            items_count=len(self.items),
            items_summary=summary,
            serialized_items=[i.to_dict() for i in self.items.values()],
            serialized_relationships=[r.to_dict() for r in self.relationships],
        )
        return self.snapshot

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_id": self.context_id,
            "task_id": self.task_id,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "version": self.version,
            "status": self.status.value,
            "items_count": len(self.items),
            "items": [i.to_dict() for i in self.items.values()],
            "relationships": [r.to_dict() for r in self.relationships],
            "constraints": [c.to_dict() for c in self.constraints],
            "source_restrictions": self.source_restrictions,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "snapshot": self.snapshot.to_dict() if self.snapshot else None,
        }
