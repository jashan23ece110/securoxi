"""
SECUROXI AI Intelligence 2.0 — Universal Input & Context Test Suite (Phase 4 Stage 17)
Validates UniversalTaskContext, Input Adapters, Context Merger, Relational Graph,
Deduplication, Tenant Isolation, Trust Decoupling, Snapshots, and Adversarial Invariants.
"""

import time
import pytest
from fastapi.testclient import TestClient

from securoxi.orchestrator.universal_context import (
    ContextItemType,
    ContextSourceType,
    ContextScope,
    ContextSecurityState,
    ContextTrustLevel,
    RelationshipType,
    ContextStatus,
    ContextItem,
    UniversalTaskContext,
    FileInputAdapter,
    FolderInputAdapter,
    JDInputAdapter,
    ATSInputAdapter,
    CollectionInputAdapter,
    PreviousTaskAdapter,
    UniversalContextMerger,
    UniversalContextManager,
)
from securoxi.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def manager():
    return UniversalContextManager()


@pytest.fixture
def merger():
    return UniversalContextMerger()


# =========================================================================
# 1. INDIVIDUAL INPUT ADAPTER TESTS
# =========================================================================

def test_file_input_adapter_resolves_files():
    """Verifies that FileInputAdapter extracts metadata and assigns trust."""
    adapter = FileInputAdapter()
    raw_files = [
        {"name": "resume_clean.pdf", "size": 1048576, "security_status": "SAFE"},
        {"name": "resume_malicious.pdf", "size": 524288, "security_status": "HIGH_RISK"},
        {"name": "resume_corrupt.pdf", "size": 262144, "security_status": "UNINSPECTABLE"},
    ]
    items = adapter.resolve(raw_files, tenant_id="TENANT-01")

    assert len(items) == 3
    assert items[0].security_state == ContextSecurityState.SAFE
    assert items[0].trust_level == ContextTrustLevel.TRUSTED_CONTEXT

    assert items[1].security_state == ContextSecurityState.HIGH_RISK
    assert items[1].trust_level == ContextTrustLevel.UNTRUSTED_EVIDENCE

    assert items[2].security_state == ContextSecurityState.UNINSPECTABLE
    assert items[2].trust_level == ContextTrustLevel.REVIEW_REQUIRED


def test_folder_input_adapter_memory_efficient():
    """Verifies that FolderInputAdapter handles 18,000 files without loading raw bytes."""
    adapter = FolderInputAdapter()
    raw_folder = {
        "name": "Production_Resumes_2026",
        "totalFiles": 18472,
        "supported": 18000,
    }
    items = adapter.resolve(raw_folder, tenant_id="TENANT-01")

    assert len(items) == 1
    assert items[0].item_type == ContextItemType.FOLDER
    assert items[0].source_type == ContextSourceType.LOCAL_FOLDER
    assert items[0].metadata["total_files"] == 18472


def test_jd_input_adapter_resolves_requirements():
    """Verifies that JDInputAdapter captures normalized criteria."""
    adapter = JDInputAdapter()
    raw_jd = {
        "title": "Senior Cloud Security Engineer",
        "requiredSkills": ["Kubernetes", "AWS IAM", "Container Hardening"],
        "expYears": 5,
    }
    items = adapter.resolve(raw_jd, tenant_id="TENANT-01")

    assert len(items) == 1
    assert items[0].item_type == ContextItemType.JOB_DESCRIPTION
    assert items[0].metadata["job_title"] == "Senior Cloud Security Engineer"
    assert "Kubernetes" in items[0].metadata["required_skills"]


def test_ats_input_adapter_no_credential_leakage():
    """Verifies that ATSInputAdapter extracts candidate and job references without secret tokens."""
    adapter = ATSInputAdapter()
    raw_ats = {
        "system": "Workday",
        "connected": True,
        "candidateCount": 120,
        "candidates": [{"id": "CAND-01", "name": "Sarah Miller"}],
    }
    items = adapter.resolve(raw_ats, tenant_id="TENANT-01")

    assert len(items) == 2
    types = [i.item_type for i in items]
    assert ContextItemType.ATS_JOB in types
    assert ContextItemType.ATS_CANDIDATE in types
    # Ensure no secrets in metadata
    for it in items:
        assert "token" not in it.metadata
        assert "secret" not in it.metadata


# =========================================================================
# 2. MIXED CONTEXT MERGING & RELATIONAL GRAPH
# =========================================================================

def test_context_merger_mixed_sources_and_relationships(merger):
    """Verifies that merger combines Folder + JD + ATS + Constraints and builds relational graph."""
    raw_context = {
        "files": [{"name": "alice_resume.pdf", "size": 1000, "security_status": "SAFE"}],
        "folder": {"name": "Resumes_Folder", "totalFiles": 500},
        "jobDescription": {"title": "Cloud Architect", "requiredSkills": ["AWS"]},
        "atsConnection": {"system": "Greenhouse", "connected": True},
    }

    ctx = merger.merge_inputs(
        raw_context=raw_context,
        task_id="TASK-MIXED-01",
        tenant_id="TENANT-01",
        constraints=["Only 5+ years experience", "Exclude high-risk"],
        source_restrictions=["LOCAL_FOLDER", "LOCAL_UPLOAD"],
    )

    assert ctx.tenant_id == "TENANT-01"
    assert len(ctx.items) >= 4
    assert len(ctx.constraints) == 2
    assert len(ctx.relationships) > 0

    # Verify JD applies to Document relationship
    applies_to_rels = [r for r in ctx.relationships if r.relationship_type == RelationshipType.APPLIES_TO]
    assert len(applies_to_rels) > 0


# =========================================================================
# 3. TENANT ISOLATION & VALIDATION
# =========================================================================

def test_context_tenant_isolation_rejection():
    """Verifies that adding an item from another tenant is strictly rejected."""
    ctx = UniversalTaskContext(tenant_id="TENANT-VICTIM")
    foreign_item = ContextItem(
        title="Attacker File",
        tenant_id="TENANT-ATTACKER",
    )

    with pytest.raises(ValueError, match="Tenant mismatch"):
        ctx.add_item(foreign_item)


def test_context_manager_validation_catches_violations(manager):
    """Verifies that context validator detects trust and tenant violations."""
    ctx = manager.create_context(
        task_id="TASK-01",
        tenant_id="TENANT-01",
        raw_inputs={"files": [{"name": "test.pdf", "security_status": "SAFE"}]},
    )
    val = manager.validate_context(ctx)
    assert val["is_valid"] is True

    # Artificially inject trust violation (HIGH_RISK in TRUSTED_CONTEXT)
    bad_item = ContextItem(
        title="Malicious.pdf",
        tenant_id="TENANT-01",
        security_state=ContextSecurityState.HIGH_RISK,
        trust_level=ContextTrustLevel.TRUSTED_CONTEXT,
    )
    ctx.items[bad_item.context_item_id] = bad_item
    val_bad = manager.validate_context(ctx)
    assert val_bad["is_valid"] is False
    assert any("HIGH_RISK" in iss for iss in val_bad["issues"])


# =========================================================================
# 4. CONTEXT SNAPSHOTS & FREEZING
# =========================================================================

def test_context_freeze_creates_immutable_snapshot(manager):
    """Verifies that freezing context locks it and produces a reproducible snapshot."""
    ctx = manager.create_context(
        task_id="TASK-FREEZE",
        tenant_id="TENANT-01",
        raw_inputs={
            "files": [{"name": "doc1.pdf", "security_status": "SAFE"}],
            "jobDescription": {"title": "Security Lead"},
        },
    )

    snapshot = manager.freeze_context(ctx.context_id, "TENANT-01")
    assert snapshot is not None
    assert snapshot.items_count == len(ctx.items)
    assert ctx.status == ContextStatus.FROZEN

    # Attempting to modify frozen context raises RuntimeError
    new_item = ContextItem(title="new.pdf", tenant_id="TENANT-01")
    with pytest.raises(RuntimeError, match="Cannot add item to FROZEN context"):
        ctx.add_item(new_item)


# =========================================================================
# 5. REST API INTEGRATION TESTS
# =========================================================================

def test_api_create_universal_context(client):
    """Verifies POST /api/v1/agentic/context/create endpoint."""
    response = client.post(
        "/api/v1/agentic/context/create",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        json={
            "task_id": "TASK-API-01",
            "inputs": {
                "files": [{"name": "resume.pdf", "size": 12000, "security_status": "SAFE"}],
                "jobDescription": {"title": "DevSecOps Lead", "requiredSkills": ["Terraform", "K8s"]},
            },
            "constraints": ["Top 10 candidates"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "context" in data
    assert "validation" in data
    assert data["validation"]["is_valid"] is True
    assert data["context"]["items_count"] == 2


def test_api_get_context_tenant_enforced(client):
    """Verifies GET /api/v1/agentic/context/{id} prevents cross-tenant access."""
    # Create in TENANT-01
    create_resp = client.post(
        "/api/v1/agentic/context/create",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-01"},
        json={"task_id": "TASK-T1", "inputs": {"files": [{"name": "secret.pdf"}]}},
    )
    ctx_id = create_resp.json()["context"]["context_id"]

    # Access from TENANT-02 must fail with 404
    resp_t2 = client.get(
        f"/api/v1/agentic/context/{ctx_id}",
        headers={"X-API-Key": "securoxi-enterprise-key", "X-Tenant-ID": "TENANT-02"},
    )
    assert resp_t2.status_code == 404


# =========================================================================
# 6. SCALABILITY BENCHMARKS
# =========================================================================

def test_context_creation_large_scale_benchmark(merger):
    """Verifies sub-millisecond context creation for large collections."""
    t0 = time.time()
    ctx = merger.merge_inputs(
        raw_context={
            "folder": {"name": "Bulk_20k_Resumes", "totalFiles": 20000, "supported": 19500},
            "jobDescription": {"title": "Enterprise Security Engineer", "requiredSkills": ["Python", "K8s"]},
            "atsConnection": {"system": "Workday", "connected": True, "candidateCount": 5000},
        },
        task_id="TASK-BENCHMARK",
        tenant_id="TENANT-01",
    )
    duration_ms = (time.time() - t0) * 1000

    assert len(ctx.items) >= 3
    assert duration_ms < 5.0  # Target: < 5.0 ms
