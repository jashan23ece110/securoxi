"""
SECUROXI AI Intelligence 2.0 — Enterprise Partner Ecosystem Models (Phase 9 Stage 60)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time
import uuid
from securoxi.enterprise.ecosystem.types import (
    PartnerType,
    PartnerVerificationStatus,
    DelegationStatus,
    PartnerScope,
)


@dataclass
class PartnerOrganization:
    """Registered partner organization."""
    partner_id: str = field(default_factory=lambda: f"PARTNER-{uuid.uuid4().hex[:8].upper()}")
    name: str = "Partner Solutions Corp"
    partner_type: PartnerType = PartnerType.INTEGRATION_PARTNER
    verification_status: PartnerVerificationStatus = PartnerVerificationStatus.UNVERIFIED
    allowed_scopes: List[PartnerScope] = field(default_factory=lambda: [PartnerScope.API_READ, PartnerScope.WORKFLOW_READ])
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class CustomerDelegation:
    """Explicit scoped delegation from an enterprise customer to a partner."""
    delegation_id: str = field(default_factory=lambda: f"DEL-{uuid.uuid4().hex[:8].upper()}")
    customer_organization_id: str = "ORG-DEFAULT"
    partner_id: str = "PARTNER-DEFAULT"
    allowed_workspaces: List[str] = field(default_factory=lambda: ["*"])
    granted_scopes: List[PartnerScope] = field(default_factory=list)
    status: DelegationStatus = DelegationStatus.ACTIVE
    expires_at: float = field(default_factory=lambda: time.time() + 86400.0)
    created_at: float = field(default_factory=time.time)


@dataclass
class PartnerApplication:
    """Registered OAuth / API application owned by a partner."""
    app_id: str = field(default_factory=lambda: f"APP-{uuid.uuid4().hex[:8].upper()}")
    partner_id: str = "PARTNER-DEFAULT"
    name: str = "ATS Connector App"
    client_id: str = field(default_factory=lambda: f"client_{uuid.uuid4().hex[:12]}")
    client_secret_hash: str = field(default_factory=lambda: uuid.uuid4().hex)
    redirect_uris: List[str] = field(default_factory=lambda: ["https://partner.example.com/oauth/callback"])
    is_active: bool = True
    created_at: float = field(default_factory=time.time)
