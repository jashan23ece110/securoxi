"""
SECUROXI AI Intelligence 2.0 — Enterprise Data Governance & Retention Models
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Set, Optional
import time
import uuid
from securoxi.enterprise.governance.types import (
    DataClassification,
    RetentionTrigger,
    RetentionState,
    LegalHoldStatus,
    ExportStatus,
)


@dataclass
class RetentionPolicy:
    """Configurable data retention rule for an organization."""
    policy_id: str = field(default_factory=lambda: f"RET-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    data_type: str = "CANDIDATE_RESUME"  # "CANDIDATE_RESUME", "SECURITY_INCIDENT", "TASK_RUN"
    retention_days: int = 90
    trigger: RetentionTrigger = RetentionTrigger.CREATION_TIME
    is_active: bool = True
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "organization_id": self.organization_id,
            "data_type": self.data_type,
            "retention_days": self.retention_days,
            "trigger": self.trigger.value,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass
class LegalHold:
    """Legal hold locking specific resources from deletion."""
    hold_id: str = field(default_factory=lambda: f"HOLD-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    resource_id: str = ""
    reason: str = "Regulatory preservation"
    created_by: str = "compliance-officer"
    status: LegalHoldStatus = LegalHoldStatus.ACTIVE
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hold_id": self.hold_id,
            "organization_id": self.organization_id,
            "resource_id": self.resource_id,
            "reason": self.reason,
            "created_by": self.created_by,
            "status": self.status.value,
            "created_at": self.created_at,
        }


@dataclass
class DataInventoryRecord:
    """Summary record in the organization data inventory."""
    record_id: str = field(default_factory=lambda: f"INV-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    resource_id: str = ""
    resource_name: str = ""
    data_type: str = "DOCUMENT"
    classification: DataClassification = DataClassification.INTERNAL
    retention_state: RetentionState = RetentionState.ACTIVE
    created_at: float = field(default_factory=time.time)


@dataclass
class DataExportRequest:
    """Time-limited, governed data export request."""
    export_id: str = field(default_factory=lambda: f"EXP-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    requested_by: str = "admin@enterprise.com"
    scope: str = "HIRING_CANDIDATES"
    status: ExportStatus = ExportStatus.READY
    download_url: str = ""
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 3600)  # 1h TTL

    def is_expired(self) -> bool:
        return time.time() > self.expires_at
