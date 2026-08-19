"""
SECUROXI AI Intelligence 2.0 — Enterprise ATS Integrations Models
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Set, Optional
import time
import uuid
from securoxi.enterprise.integrations.types import (
    ATSProviderType,
    IntegrationStatus,
    IntegrationCapability,
    SyncStatus,
)


@dataclass
class EnterpriseIntegration:
    """Strongly typed enterprise ATS integration configuration (secrets held separately)."""
    integration_id: str = field(default_factory=lambda: f"INT-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    workspace_id: Optional[str] = None
    provider_type: ATSProviderType = ATSProviderType.GREENHOUSE
    status: IntegrationStatus = IntegrationStatus.CONNECTED
    capabilities: Set[IntegrationCapability] = field(default_factory=lambda: {
        IntegrationCapability.READ_JOBS,
        IntegrationCapability.READ_CANDIDATES,
        IntegrationCapability.READ_RESUMES,
    })
    created_at: float = field(default_factory=time.time)
    last_sync_timestamp: Optional[float] = None
    sync_status: SyncStatus = SyncStatus.IDLE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "integration_id": self.integration_id,
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "provider_type": self.provider_type.value,
            "status": self.status.value,
            "capabilities": [c.value for c in self.capabilities],
            "created_at": self.created_at,
            "last_sync_timestamp": self.last_sync_timestamp,
            "sync_status": self.sync_status.value,
        }


@dataclass
class ExternalJob:
    """Normalized ATS Job description entity."""
    job_id: str
    integration_id: str
    organization_id: str
    external_id: str
    title: str
    status: str = "OPEN"
    required_skills: List[str] = field(default_factory=list)
    description_text: str = ""


@dataclass
class ExternalCandidate:
    """Normalized ATS Candidate entity."""
    candidate_id: str
    integration_id: str
    organization_id: str
    external_id: str
    name: str
    current_stage: str = "APPLIED"
    resume_path: Optional[str] = None
    extracted_skills: List[str] = field(default_factory=list)


@dataclass
class ATSWriteProposal:
    """Governance proposal for an ATS state mutation (e.g. stage promotion)."""
    proposal_id: str = field(default_factory=lambda: f"PROP-{uuid.uuid4().hex[:8].upper()}")
    integration_id: str = "INT-DEFAULT"
    organization_id: str = "ORG-DEFAULT"
    candidate_id: str = "CAND-DEFAULT"
    target_stage: str = "INTERVIEW"
    reason: str = "Screening passed"
    is_approved: bool = False
    approved_by: Optional[str] = None
    executed: bool = False
