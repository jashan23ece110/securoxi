"""
SECUROXI AI Intelligence 2.0 — Autonomous Hiring Intelligence Models (Phase 8 Stage 47)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
import time
import uuid
from securoxi.enterprise.hiring.types import (
    ChangeSignificance,
    CandidateChangeType,
    HiringSignalType,
    WatchStatus,
    RecommendationStatus,
)


@dataclass
class CandidateChange:
    """Record of a detected candidate/resume/ATS/security change."""
    change_id: str = field(default_factory=lambda: f"CHG-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-HIRING"
    candidate_id: str = "CAND-001"
    change_type: CandidateChangeType = CandidateChangeType.RESUME_UPDATED
    significance: ChangeSignificance = ChangeSignificance.MATERIAL
    changed_fields: List[str] = field(default_factory=list)
    previous_state: Dict[str, Any] = field(default_factory=dict)
    new_state: Dict[str, Any] = field(default_factory=dict)
    detected_at: float = field(default_factory=time.time)
    security_state: str = "SAFE"


@dataclass
class CandidateWatch:
    """Watchlist rule for monitoring specific candidate state transitions."""
    watch_id: str = field(default_factory=lambda: f"WATCH-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-HIRING"
    candidate_id: str = "CAND-001"
    job_id: str = "JOB-001"
    created_by: str = "USER-DEFAULT"
    status: WatchStatus = WatchStatus.ACTIVE
    conditions: List[str] = field(default_factory=lambda: ["RANK_CHANGE", "SECURITY_CHANGE"])
    created_at: float = field(default_factory=time.time)


@dataclass
class JobWatch:
    """Watchlist rule for monitoring an entire job pipeline."""
    watch_id: str = field(default_factory=lambda: f"JOBWATCH-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-HIRING"
    job_id: str = "JOB-001"
    target_top_k: int = 20
    status: WatchStatus = WatchStatus.ACTIVE
    created_by: str = "USER-DEFAULT"
    created_at: float = field(default_factory=time.time)


@dataclass
class HiringRecommendation:
    """Grounded, non-authoritative candidate recommendation."""
    recommendation_id: str = field(default_factory=lambda: f"REC-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-HIRING"
    candidate_id: str = "CAND-001"
    job_id: str = "JOB-001"
    suggested_action: str = "ADVANCE_TO_INTERVIEW"
    previous_rank: Optional[int] = 24
    new_rank: int = 5
    rank_delta: int = 19
    fit_score: float = 92.0
    security_state: str = "SAFE"
    confidence: float = 0.90
    reason: str = "Candidate added verified Kubernetes experience, entering top 5"
    supporting_evidence: List[str] = field(default_factory=list)
    status: RecommendationStatus = RecommendationStatus.PROPOSED
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 86400 * 7)  # 7 days TTL


@dataclass
class CandidateEvaluationState:
    """Evaluation snapshot for tracking stale vs current status."""
    candidate_id: str
    job_id: str
    fit_score: float
    rank: int
    security_state: str = "SAFE"
    is_stale: bool = False
    evaluation_version: str = "v2.1"
    updated_at: float = field(default_factory=time.time)
