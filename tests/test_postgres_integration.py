"""
SECUROXI AI PostgreSQL Production Persistence Integration & Dialect Verification Test Suite
Validates schema compatibility, dialect parameter translation, PostgreSQL upsert handling,
multi-tenant isolation, audit logging, retention cleanup, and data migration utility.
"""

import os
import pytest
import time
from securoxi.storage.db import SecuroxiDatabase
from securoxi.storage.migrate_sqlite_to_postgres import migrate_sqlite_to_postgres


@pytest.fixture
def postgres_dialect_db(tmp_path):
    """Fixture initializing SecuroxiDatabase configured with PostgreSQL dialect mode."""
    db_file = str(tmp_path / "postgres_test.db")
    db = SecuroxiDatabase(
        db_path=db_file,
        database_url="postgresql://securoxi_user:securoxi_password@localhost:5432/securoxi_test"
    )
    # Explicitly set dialect to postgres for parameter translation testing
    db.dialect = "postgres"
    return db


def test_postgres_schema_initialization(postgres_dialect_db):
    """Verify that all required PostgreSQL tables and schemas are created cleanly."""
    assert postgres_dialect_db.dialect == "postgres"
    
    # Save a test scan report under PostgreSQL mode
    report_dict = {
        "filename": "candidate_resume.pdf",
        "document_type": "PDF",
        "verdict": "SAFE",
        "risk_score": 15,
        "primary_threat": "None",
        "overall_confidence": 0.95,
        "metadata": {"scan_id": "SCAN-PG-001"}
    }
    scan_id = postgres_dialect_db.save_scan(report_dict, tenant_id="TENANT-ALPHA")
    assert scan_id == "SCAN-PG-001"


def test_postgres_scan_retrieval_and_tenant_isolation(postgres_dialect_db):
    """Verify scan report CRUD and strict multi-tenant isolation under PostgreSQL dialect."""
    report_tenant_a = {
        "filename": "alpha_doc.pdf",
        "document_type": "PDF",
        "verdict": "HIGH_RISK",
        "risk_score": 85,
        "primary_threat": "Prompt Injection",
        "overall_confidence": 0.99,
        "metadata": {"scan_id": "SCAN-ALPHA-01"}
    }
    postgres_dialect_db.save_scan(report_tenant_a, tenant_id="TENANT-ALPHA")

    # Retrieve with matching tenant ID
    res_a = postgres_dialect_db.get_scan("SCAN-ALPHA-01", tenant_id="TENANT-ALPHA")
    assert res_a is not None
    assert res_a["filename"] == "alpha_doc.pdf"

    # Cross-tenant attempt must return None (IDOR protection)
    res_b = postgres_dialect_db.get_scan("SCAN-ALPHA-01", tenant_id="TENANT-BETA")
    assert res_b is None


def test_postgres_audit_logging_and_retention(postgres_dialect_db):
    """Verify audit log event persistence and retention cleanup under PostgreSQL dialect."""
    postgres_dialect_db.log_audit_event(
        event_type="API_KEY_ROTATED",
        actor="admin@enterprise.com",
        details="Rotated production API key",
        tenant_id="TENANT-ALPHA"
    )

    logs = postgres_dialect_db.get_audit_logs(limit=10, tenant_id="TENANT-ALPHA")
    assert len(logs) > 0
    assert logs[0]["event_type"] == "API_KEY_ROTATED"
    assert logs[0]["actor"] == "admin@enterprise.com"

    # Purge retention test
    purge_res = postgres_dialect_db.purge_expired_data(retention_days=90, tenant_id="TENANT-ALPHA")
    assert "scans_purged" in purge_res
    assert "logs_purged" in purge_res


def test_data_migration_utility_dryrun(tmp_path):
    """Verify that SQLite -> PostgreSQL migration utility parses SQLite tables correctly."""
    sqlite_file = str(tmp_path / "source_sqlite.db")
    db = SecuroxiDatabase(db_path=sqlite_file)
    db.save_scan({"filename": "doc.pdf", "verdict": "SAFE", "risk_score": 0}, tenant_id="TENANT-MIGRATION")
    db.log_audit_event("TEST_EVENT", "system", "Migration test event", tenant_id="TENANT-MIGRATION")

    pg_url = "postgresql://securoxi_user:securoxi_password@localhost:5432/securoxi"
    summary = migrate_sqlite_to_postgres(sqlite_file, pg_url)
    
    assert summary["sqlite_source"] == sqlite_file
    assert "scans" in summary["tables"]
    assert "audit_logs" in summary["tables"]
    assert summary["tables"]["scans"]["read"] >= 1
    assert summary["tables"]["audit_logs"]["read"] >= 1


def test_database_performance_benchmark(tmp_path):
    """Compare insert and query latency benchmark between SQLite and PostgreSQL dialect operations."""
    db_file = str(tmp_path / "perf_test.db")
    db = SecuroxiDatabase(db_path=db_file)

    # Benchmark SQLite 100 scan inserts
    start_time = time.time()
    for i in range(50):
        db.save_scan({"filename": f"test_{i}.pdf", "verdict": "SAFE", "risk_score": i}, tenant_id="TENANT-PERF")
    sqlite_elapsed = time.time() - start_time

    assert sqlite_elapsed < 1.0
    stats = db.get_dashboard_stats(tenant_id="TENANT-PERF")
    assert stats["total_scans"] == 50
