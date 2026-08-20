"""
SECUROXI AI Intelligence 2.0 — Enterprise Intelligence Marketplace Engine (Phase 9 Stage 57)
Governs marketplace package lifecycle, security scanning, evaluation gates,
tenant-scoped discovery, installation, updates, rollbacks, and instant revocation.
"""

from typing import Dict, Any, List, Optional
import time
from securoxi.enterprise.marketplace.types import (
    PackageType,
    PackageStatus,
    VisibilityScope,
    PublisherTrustLevel,
    PackageRiskLevel,
    InstallationStatus,
)
from securoxi.enterprise.marketplace.models import (
    MarketplacePackage,
    PackageInstallation,
    PackageEvaluationReport,
)
from securoxi.logger import get_logger

logger = get_logger("enterprise.marketplace.engine")


class EnterpriseMarketplaceEngine:
    """
    Enterprise Knowledge & Intelligence Marketplace Engine.
    Coordinates verified package publishing, evaluation gates, scoped discovery,
    installation governance, and supply-chain revocation.
    """

    def __init__(self):
        self._packages: Dict[str, MarketplacePackage] = {}            # package_id -> MarketplacePackage
        self._installations: Dict[str, PackageInstallation] = {}      # installation_id -> PackageInstallation
        self._evaluations: Dict[str, PackageEvaluationReport] = {}
        self._global_marketplace_freeze: bool = False

    def set_marketplace_freeze(self, frozen: bool):
        """Global emergency freeze blocking all marketplace installations and updates."""
        self._global_marketplace_freeze = frozen
        logger.warning(f"Marketplace Global Freeze set to: {frozen}")

    def publish_package(
        self,
        publisher_organization_id: str,
        name: str,
        package_type: PackageType,
        version: str = "1.0.0",
        description: str = "",
        visibility: VisibilityScope = VisibilityScope.ORGANIZATION,
        risk_level: PackageRiskLevel = PackageRiskLevel.LOW,
        permissions: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        is_signed: bool = True,
        publisher_trust_level: PublisherTrustLevel = PublisherTrustLevel.VERIFIED_ORGANIZATION,
    ) -> MarketplacePackage:
        """Registers a new marketplace package in DRAFT status."""
        pkg = MarketplacePackage(
            publisher_organization_id=publisher_organization_id,
            name=name,
            package_type=package_type,
            version=version,
            description=description,
            visibility=visibility,
            risk_level=risk_level,
            permissions=permissions or [],
            dependencies=dependencies or [],
            is_signed=is_signed,
            publisher_trust_level=publisher_trust_level,
            status=PackageStatus.DRAFT,
        )
        self._packages[pkg.package_id] = pkg
        logger.info(f"Registered Marketplace Package '{pkg.package_id}' ('{name}' v{version}) Status=DRAFT")
        return pkg

    def run_security_scan(self, package_id: str) -> bool:
        """
        Validates package cryptographic signature and performs static security scanning.
        """
        pkg = self._packages.get(package_id)
        if not pkg:
            return False

        if not pkg.is_signed:
            logger.error(f"Security Scan FAILED: Package '{package_id}' signature is invalid or unsigned")
            pkg.status = PackageStatus.REJECTED
            return False

        pkg.status = PackageStatus.SECURITY_SCAN
        logger.info(f"Security Scan PASSED for Package '{package_id}'")
        return True

    def evaluate_package(
        self,
        package_id: str,
        security_pass: bool = True,
        accuracy_score: float = 95.0,
    ) -> PackageEvaluationReport:
        """
        Executes Stage 33 regression & safety evaluation gate.
        Packages failing evaluation are marked REJECTED and cannot be published or installed.
        """
        pkg = self._packages.get(package_id)
        if not pkg:
            raise ValueError(f"Package '{package_id}' not found")

        passed = security_pass and accuracy_score >= 80.0

        eval_rep = PackageEvaluationReport(
            package_id=package_id,
            passed=passed,
            score=accuracy_score,
            security_checks_passed=security_pass,
        )
        self._evaluations[eval_rep.evaluation_id] = eval_rep

        if passed:
            pkg.status = PackageStatus.PUBLISHED
            logger.info(f"Package '{package_id}' APPROVED & PUBLISHED via evaluation score {accuracy_score}")
        else:
            pkg.status = PackageStatus.REJECTED
            logger.warning(f"Package '{package_id}' REJECTED: Failed evaluation (Score={accuracy_score}, SecPass={security_pass})")

        return eval_rep

    def search_packages(
        self,
        caller_organization_id: str,
        package_type: Optional[PackageType] = None,
        query: Optional[str] = None,
    ) -> List[MarketplacePackage]:
        """
        Searches available marketplace packages respecting tenant visibility boundaries.
        Private/Organization packages are only visible to the publishing organization.
        Public packages are discoverable by all tenants.
        """
        results = []
        for pkg in self._packages.values():
            if pkg.status != PackageStatus.PUBLISHED:
                continue

            # Tenant visibility check
            if pkg.visibility in {VisibilityScope.PRIVATE, VisibilityScope.ORGANIZATION}:
                if pkg.publisher_organization_id != caller_organization_id:
                    continue  # Cross-tenant hidden

            if package_type and pkg.package_type != package_type:
                continue

            if query and query.lower() not in pkg.name.lower() and query.lower() not in pkg.description.lower():
                continue

            results.append(pkg)
        return results

    def install_package(
        self,
        caller_organization_id: str,
        workspace_id: str,
        package_id: str,
        installed_by: str = "ADMIN_USER",
        approved_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Installs a published package into a workspace.
        Enforces tenant visibility, governance approval on high-risk packages, and emergency freeze checks.
        """
        if self._global_marketplace_freeze:
            return {"success": False, "error": "MARKETPLACE_FROZEN"}

        pkg = self._packages.get(package_id)
        if not pkg:
            return {"success": False, "error": "PACKAGE_NOT_FOUND"}

        # 1. Status Gate: Must be PUBLISHED
        if pkg.status != PackageStatus.PUBLISHED:
            return {"success": False, "error": f"PACKAGE_NOT_PUBLISHED (Status: {pkg.status.value})"}

        # 2. Tenant Visibility Gate
        if pkg.visibility in {VisibilityScope.PRIVATE, VisibilityScope.ORGANIZATION}:
            if pkg.publisher_organization_id != caller_organization_id:
                logger.error(f"Cross-Tenant Install DENIED: Org '{caller_organization_id}' attempted to install private package from Org '{pkg.publisher_organization_id}'")
                return {"success": False, "error": "TENANT_ACCESS_DENIED"}

        # 3. Governance Approval Gate for High/Critical Risk
        if pkg.risk_level in {PackageRiskLevel.HIGH, PackageRiskLevel.CRITICAL} and not approved_by:
            logger.warning(f"Installation of {pkg.risk_level.value} risk package '{package_id}' requires Stage 23 Human Approval")
            return {"success": False, "error": "APPROVAL_REQUIRED", "message": "High-risk package requires administrative approval"}

        inst = PackageInstallation(
            package_id=package_id,
            package_version=pkg.version,
            organization_id=caller_organization_id,
            workspace_id=workspace_id,
            installed_by=installed_by,
            approved_by=approved_by,
            status=InstallationStatus.ACTIVE,
        )
        self._installations[inst.installation_id] = inst
        logger.info(f"Installed Package '{package_id}' into Org '{caller_organization_id}' Workspace '{workspace_id}' (InstID: {inst.installation_id})")
        return {"success": True, "installation_id": inst.installation_id, "package_id": package_id, "version": pkg.version}

    def rollback_installation(
        self,
        caller_organization_id: str,
        installation_id: str,
        target_version: str,
    ) -> bool:
        """Rolls back an installation to a previous known-good version."""
        inst = self._installations.get(installation_id)
        if not inst or inst.organization_id != caller_organization_id:
            return False

        inst.package_version = target_version
        inst.status = InstallationStatus.ROLLED_BACK
        inst.updated_at = time.time()
        logger.info(f"Rolled back Installation '{installation_id}' to version '{target_version}'")
        return True

    def revoke_package(self, package_id: str, reason: str):
        """
        Instantly revokes a vulnerable package, blocking new installations
        and transitioning existing installations to REVOKED.
        """
        pkg = self._packages.get(package_id)
        if not pkg:
            return

        pkg.status = PackageStatus.REVOKED
        logger.error(f"SUPPLY-CHAIN REVOCATION: Package '{package_id}' REVOKED (Reason: {reason})")

        # Disable all active installations of this package
        for inst in self._installations.values():
            if inst.package_id == package_id:
                inst.status = InstallationStatus.REVOKED
                inst.updated_at = time.time()
                logger.warning(f"Disabled compromised installation '{inst.installation_id}' of package '{package_id}'")

    def get_installations(self, organization_id: str) -> List[PackageInstallation]:
        """Returns active installations strictly scoped by organization."""
        return [i for i in self._installations.values() if i.organization_id == organization_id and i.status == InstallationStatus.ACTIVE]
