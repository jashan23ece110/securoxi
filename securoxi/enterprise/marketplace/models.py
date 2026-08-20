"""
SECUROXI AI Intelligence 2.0 — Enterprise Intelligence Marketplace Models (Phase 9 Stage 57)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time
import uuid
from securoxi.enterprise.marketplace.types import (
    PackageType,
    PackageStatus,
    VisibilityScope,
    PublisherTrustLevel,
    PackageRiskLevel,
    InstallationStatus,
)


@dataclass
class MarketplacePackage:
    """Canonical marketplace package definition."""
    package_id: str = field(default_factory=lambda: f"PKG-{uuid.uuid4().hex[:8].upper()}")
    package_type: PackageType = PackageType.CUSTOM_TOOL
    publisher_id: str = "PUB-DEFAULT"
    publisher_organization_id: str = "ORG-DEFAULT"
    publisher_trust_level: PublisherTrustLevel = PublisherTrustLevel.VERIFIED_ORGANIZATION
    name: str = "Candidate Screening Intelligence Pack"
    description: str = "Verified skills and tool connectors for candidate evaluation"
    version: str = "1.0.0"
    status: PackageStatus = PackageStatus.DRAFT
    visibility: VisibilityScope = VisibilityScope.ORGANIZATION
    risk_level: PackageRiskLevel = PackageRiskLevel.LOW
    permissions: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    autonomy_level: str = "L2_HUMAN_APPROVAL_REQUIRED"
    digest_sha256: str = field(default_factory=lambda: uuid.uuid4().hex)
    is_signed: bool = True
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class PackageInstallation:
    """Record of an installed marketplace package in a tenant organization/workspace."""
    installation_id: str = field(default_factory=lambda: f"INST-{uuid.uuid4().hex[:8].upper()}")
    package_id: str = "PKG-DEFAULT"
    package_version: str = "1.0.0"
    organization_id: str = "ORG-DEFAULT"
    workspace_id: str = "WS-DEFAULT"
    status: InstallationStatus = InstallationStatus.ACTIVE
    installed_by: str = "ADMIN_USER"
    approved_by: Optional[str] = None
    installed_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class PackageEvaluationReport:
    """Stage 33 regression & safety evaluation outcome for marketplace admission."""
    evaluation_id: str = field(default_factory=lambda: f"EVAL-{uuid.uuid4().hex[:8].upper()}")
    package_id: str = "PKG-DEFAULT"
    passed: bool = True
    score: float = 100.0
    security_checks_passed: bool = True
    evaluated_at: float = field(default_factory=time.time)
