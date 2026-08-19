"""
SECUROXI AI Intelligence 2.0 — Enterprise Data Governance & Retention Test Suite (Stage 39)
Validates data inventory tracking, classification, legal holds, dependency-aware safe deletion,
time-bounded data exports, and multi-tenant isolation.
"""

import pytest
import time
from securoxi.enterprise.governance import (
    EnterpriseDataGovernanceManager,
    DataClassification,
    RetentionState,
    RetentionPolicy,
    LegalHoldStatus,
    ExportStatus,
)


# =========================================================================
# 1. DATA INVENTORY & CLASSIFICATION
# =========================================================================

def test_inventory_and_classification_registration():
    """Verifies registering items into the organization data inventory with explicit classification."""
    manager = EnterpriseDataGovernanceManager()

    item = manager.register_inventory_item(
        organization_id="ORG-ACME",
        resource_id="DOC-RESUME-001",
        resource_name="Candidate_Resume.pdf",
        data_type="CANDIDATE_DATA",
        classification=DataClassification.RESTRICTED,
    )

    assert item.organization_id == "ORG-ACME"
    assert item.classification == DataClassification.RESTRICTED
    assert item.retention_state == RetentionState.ACTIVE


# =========================================================================
# 2. LEGAL HOLD ENFORCEMENT & DELETION BLOCKING
# =========================================================================

def test_legal_hold_blocks_deletion():
    """Verifies that an active legal hold strictly blocks deletion until released."""
    manager = EnterpriseDataGovernanceManager()

    manager.register_inventory_item(
        organization_id="ORG-ACME",
        resource_id="DOC-INCIDENT-001",
        resource_name="Incident_Forensics.json",
        data_type="SECURITY_EVIDENCE",
    )

    # Apply Legal Hold
    hold = manager.apply_legal_hold(
        organization_id="ORG-ACME",
        resource_id="DOC-INCIDENT-001",
        reason="Litigation preservation",
        created_by="legal-counsel@acme.com",
    )
    assert hold.status == LegalHoldStatus.ACTIVE

    # Attempt Deletion -> MUST FAIL
    res = manager.execute_safe_deletion("ORG-ACME", "DOC-INCIDENT-001")
    assert res["success"] is False
    assert "Legal Hold" in res["reason"]

    # Release Legal Hold
    manager.release_legal_hold(hold.hold_id, released_by="legal-counsel@acme.com")

    # Attempt Deletion again -> SUCCESS
    res_after = manager.execute_safe_deletion("ORG-ACME", "DOC-INCIDENT-001")
    assert res_after["success"] is True
    assert res_after["status"] == "DELETED"


# =========================================================================
# 3. DEPENDENCY-AWARE DELETION
# =========================================================================

def test_dependency_aware_deletion():
    """Verifies that items referenced by active investigations cannot be deleted."""
    manager = EnterpriseDataGovernanceManager()

    manager.register_inventory_item(
        organization_id="ORG-ACME",
        resource_id="DOC-EVIDENCE-002",
        resource_name="Packet_Capture.pcap",
    )

    # Register active referencing dependency
    manager.register_dependency("DOC-EVIDENCE-002", referencing_id="INCIDENT-SOC-404")

    # Attempt Deletion -> MUST FAIL due to active dependency
    res = manager.execute_safe_deletion("ORG-ACME", "DOC-EVIDENCE-002")
    assert res["success"] is False
    assert "dependencies exist" in res["reason"]

    # Clear dependency
    manager.remove_dependency("DOC-EVIDENCE-002", referencing_id="INCIDENT-SOC-404")

    # Attempt Deletion -> SUCCESS
    res_after = manager.execute_safe_deletion("ORG-ACME", "DOC-EVIDENCE-002")
    assert res_after["success"] is True


# =========================================================================
# 4. TIME-BOUNDED DATA EXPORTS & EXPIRATION
# =========================================================================

def test_data_export_governance_and_expiration():
    """Verifies governed export creation, organization isolation, and TTL expiration."""
    manager = EnterpriseDataGovernanceManager()

    export = manager.request_export(
        organization_id="ORG-ACME",
        requested_by="compliance@acme.com",
        scope="AUDIT_LOGS",
        ttl_seconds=1,  # 1 second TTL
    )
    assert export.status == ExportStatus.READY

    # Access by same organization -> Allowed
    accessed = manager.access_export(export.export_id, "ORG-ACME")
    assert accessed is not None

    # Access by another organization -> DENIED
    cross_org = manager.access_export(export.export_id, "ORG-OTHER")
    assert cross_org is None

    # Wait for expiration
    time.sleep(1.1)
    expired = manager.access_export(export.export_id, "ORG-ACME")
    assert expired is None
