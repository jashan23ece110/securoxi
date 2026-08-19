"""
SECUROXI AI Intelligence 2.0 — Continuous Knowledge Intelligence Models (Phase 8 Stage 48)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
import time
import uuid
from securoxi.enterprise.knowledge.types import (
    SourceAuthority,
    AdmissionDecision,
    KnowledgeFreshness,
    KnowledgeChangeType,
)


@dataclass
class KnowledgeSource:
    """Canonical representation of an enterprise knowledge source."""
    source_id: str = field(default_factory=lambda: f"SRC-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-DEFAULT"
    title: str = "Enterprise Document"
    authority: SourceAuthority = SourceAuthority.VERIFIED
    admission: AdmissionDecision = AdmissionDecision.ADMITTED
    freshness: KnowledgeFreshness = KnowledgeFreshness.CURRENT
    security_state: str = "SAFE"
    classification: str = "INTERNAL"
    version: int = 1
    content_hash: str = "hash-v1"
    raw_content: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class KnowledgeChunk:
    """Chunk of an admitted knowledge source with embedding metadata."""
    chunk_id: str = field(default_factory=lambda: f"CHK-{uuid.uuid4().hex[:8].upper()}")
    source_id: str = "SRC-DEFAULT"
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-DEFAULT"
    content: str = ""
    is_valid: bool = True
    embedding_version: str = "v3-hybrid"
    indexed_at: float = field(default_factory=time.time)


@dataclass
class KnowledgeConflict:
    """Detected conflict between multiple knowledge sources."""
    conflict_id: str = field(default_factory=lambda: f"CONF-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-DEFAULT"
    topic: str = "Data Retention Policy"
    conflicting_source_ids: List[str] = field(default_factory=list)
    explanation: str = "Discrepancy detected across sources"
    resolved_source_id: Optional[str] = None
    detected_at: float = field(default_factory=time.time)


@dataclass
class QuestionSubscription:
    """User/Workspace subscription tracking answers to a live question."""
    subscription_id: str = field(default_factory=lambda: f"SUB-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-DEFAULT"
    user_id: str = "USER-DEFAULT"
    question: str = "What is the official retention period?"
    current_answer: str = "Retention is 90 days as per security policy v2"
    dependent_source_ids: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: float = field(default_factory=time.time)
    last_evaluated_at: float = field(default_factory=time.time)


@dataclass
class KnowledgeAnswer:
    """Answer evaluated against continuous knowledge with provenance."""
    question: str
    answer: str
    confidence: float
    sources: List[str]
    freshness: KnowledgeFreshness = KnowledgeFreshness.CURRENT
    has_conflicts: bool = False
