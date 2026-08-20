"""
SECUROXI AI Intelligence 2.0 — Enterprise Intelligence Marketplace Test Suite (Phase 9 Stage 57)
Validates package publishing, signing verification, evaluation gates, tenant-scoped search,
governed installation of high-risk assets, rollback, and supply-chain revocation.
"""

import pytest
from securoxi.enterprise.marketplace import (
    EnterpriseMarketplaceEngine,
    PackageType,
    PackageStatus,
    VisibilityScope,
    PackageRiskLevel,
    InstallationStatus,
)


# =========================================================================
# 1. PUBLISHING, SIGNATURE SCANNING & EVALUATION GATES
# =========================================================================

def test_marketplace_publishing_and_evaluation_gates():
    """Verifies that packages must be signed and pass Stage 33 evaluation before publication."""
    mkt = EnterpriseMarketplaceEngine()

    # 1. Unsigned Package -> Security Scan rejects
    pkg_unsigned = mkt.publish_package(
        publisher_organization_id="ORG-ALPHA",
        name="Unsigned Tool",
        package_type=PackageType.CUSTOM_TOOL,
        is_signed=False,
    )
    assert mkt.run_security_scan(pkg_unsigned.package_id) is False
    assert pkg_unsigned.status == PackageStatus.REJECTED

    # 2. Signed Package -> Security Scan passes
    pkg_signed = mkt.publish_package(
        publisher_organization_id="ORG-ALPHA",
        name="Candidate Screening Agent",
        package_type=PackageType.CUSTOM_AGENT,
        is_signed=True,
    )
    assert mkt.run_security_scan(pkg_signed.package_id) is True

    # 3. Failed Evaluation -> Status is REJECTED
    eval_fail = mkt.evaluate_package(pkg_signed.package_id, security_pass=False, accuracy_score=50.0)
    assert eval_fail.passed is False
    assert pkg_signed.status == PackageStatus.REJECTED

    # 4. Passed Evaluation -> Status becomes PUBLISHED
    eval_pass = mkt.evaluate_package(pkg_signed.package_id, security_pass=True, accuracy_score=95.0)
    assert eval_pass.passed is True
    assert pkg_signed.status == PackageStatus.PUBLISHED


# =========================================================================
# 2. SCOPED DISCOVERY & CROSS-TENANT ISOLATION
# =========================================================================

def test_marketplace_scoped_discovery_and_tenant_isolation():
    """Verifies private packages are only discoverable by publisher org, while public packages are visible."""
    mkt = EnterpriseMarketplaceEngine()

    # 1. Org Alpha publishes private package
    pkg_alpha = mkt.publish_package(
        publisher_organization_id="ORG-ALPHA",
        name="Alpha Private Skills",
        package_type=PackageType.CUSTOM_SKILL,
        visibility=VisibilityScope.ORGANIZATION,
    )
    mkt.evaluate_package(pkg_alpha.package_id, security_pass=True, accuracy_score=90.0)

    # 2. Org Alpha publishes public package
    pkg_public = mkt.publish_package(
        publisher_organization_id="ORG-ALPHA",
        name="Public Screening Workflow",
        package_type=PackageType.WORKFLOW_TEMPLATE,
        visibility=VisibilityScope.PUBLIC,
    )
    mkt.evaluate_package(pkg_public.package_id, security_pass=True, accuracy_score=90.0)

    # Discovery by Org Alpha -> Sees both
    results_alpha = mkt.search_packages("ORG-ALPHA")
    assert len(results_alpha) == 2

    # Discovery by Org Beta -> Sees only the PUBLIC package
    results_beta = mkt.search_packages("ORG-BETA")
    assert len(results_beta) == 1
    assert results_beta[0].package_id == pkg_public.package_id

    # Cross-tenant install of private package -> DENIED
    install_denied = mkt.install_package(
        caller_organization_id="ORG-BETA",
        workspace_id="WS-BETA",
        package_id=pkg_alpha.package_id,
    )
    assert install_denied["success"] is False
    assert install_denied["error"] == "TENANT_ACCESS_DENIED"


# =========================================================================
# 3. GOVERNED INSTALLATION, ROLLBACK & SUPPLY-CHAIN REVOCATION
# =========================================================================

def test_governed_installation_rollback_and_revocation():
    """Verifies high-risk approvals, installation rollback, and instant supply-chain revocation."""
    mkt = EnterpriseMarketplaceEngine()

    # 1. Publish High-Risk Connector Package
    pkg = mkt.publish_package(
        publisher_organization_id="ORG-ALPHA",
        name="ATS Write Connector",
        package_type=PackageType.CUSTOM_CONNECTOR,
        risk_level=PackageRiskLevel.HIGH,
        visibility=VisibilityScope.ORGANIZATION,
    )
    mkt.evaluate_package(pkg.package_id, security_pass=True, accuracy_score=95.0)

    # 2. Install without approval -> APPROVAL_REQUIRED
    inst_unapproved = mkt.install_package(
        caller_organization_id="ORG-ALPHA",
        workspace_id="WS-MAIN",
        package_id=pkg.package_id,
        installed_by="USER-1",
    )
    assert inst_unapproved["success"] is False
    assert inst_unapproved["error"] == "APPROVAL_REQUIRED"

    # 3. Install with approval -> SUCCESS
    inst_approved = mkt.install_package(
        caller_organization_id="ORG-ALPHA",
        workspace_id="WS-MAIN",
        package_id=pkg.package_id,
        installed_by="USER-1",
        approved_by="SEC_ADMIN",
    )
    assert inst_approved["success"] is True
    inst_id = inst_approved["installation_id"]

    # 4. Rollback Installation to v0.9.0
    assert mkt.rollback_installation("ORG-ALPHA", inst_id, "0.9.0") is True

    # 5. Supply-Chain Revocation -> Disables active installation
    mkt.revoke_package(pkg.package_id, reason="CVE-2026-9999 Dependency Vulnerability")
    assert pkg.status == PackageStatus.REVOKED

    # Active installations list should now be empty
    active_insts = mkt.get_installations("ORG-ALPHA")
    assert len(active_insts) == 0

    # 6. Global Freeze Switch -> Blocks all installs
    mkt.set_marketplace_freeze(True)
    inst_frozen = mkt.install_package("ORG-ALPHA", "WS-MAIN", pkg.package_id)
    assert inst_frozen["success"] is False
    assert inst_frozen["error"] == "MARKETPLACE_FROZEN"
