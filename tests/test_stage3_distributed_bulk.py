"""
SECUROXI AI Document Intelligence Stage 3 — Distributed Bulk Processing Test Suite
Validates bulk job model, SHA-256 idempotency deduplication, worker task consumption,
retry/DLQ routing for poison documents, and multi-tenant job isolation.
"""

import os
import tempfile
import fitz  # PyMuPDF
import pytest
from fastapi.testclient import TestClient

from securoxi.api.app import app
from securoxi.brain.bulk_models import BulkBatchJob, BulkDocumentTask, JobStatus, TaskStatus
from securoxi.brain.bulk_worker import SecuroxiBulkManager

client = TestClient(app)


@pytest.fixture
def temp_pdf_files():
    """Create a pair of temporary PDF files."""
    paths = []
    for i in range(2):
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50 + i * 20), f"Sample Document #{i+1} for Bulk Worker Testing", fontsize=12)
        doc.save(path)
        doc.close()
        paths.append(path)

    yield paths

    for path in paths:
        if os.path.exists(path):
            os.remove(path)


def test_bulk_batch_job_model_lifecycle():
    """Verify BulkBatchJob state tracking and progress updates."""
    job = BulkBatchJob(
        job_id="JOB-TEST-01",
        batch_id="BATCH-TEST-01",
        tenant_id="TENANT-ALPHA",
        source="TEST",
        total_documents=2
    )

    assert job.status == JobStatus.QUEUED
    assert job.progress_pct == 0.0

    job.completed_documents = 1
    job.update_progress()
    assert job.progress_pct == 50.0

    job.completed_documents = 2
    job.update_progress()
    assert job.progress_pct == 100.0
    assert job.status == JobStatus.COMPLETE


def test_idempotency_deduplication(temp_pdf_files):
    """Verify duplicate files with identical SHA-256 hashes are deduplicated upon batch creation."""
    manager = SecuroxiBulkManager()
    # Pass duplicate file path twice
    duplicated_paths = [temp_pdf_files[0], temp_pdf_files[0]]

    job = manager.create_batch_job(duplicated_paths, tenant_id="TENANT-BETA")
    assert job.total_documents == 1  # Deduplicated from 2 to 1


def test_batch_worker_execution_and_verdict_aggregation(temp_pdf_files):
    """Verify worker pool processes tasks synchronously and aggregates verdict statistics."""
    manager = SecuroxiBulkManager()
    job = manager.create_batch_job(temp_pdf_files, tenant_id="TENANT-GAMMA")

    processed_job = manager.process_batch_sync(job.batch_id, max_workers=2)
    assert processed_job.status in [JobStatus.COMPLETE, JobStatus.PARTIAL]
    assert processed_job.completed_documents == 2
    assert processed_job.progress_pct == 100.0


def test_poison_document_dlq_routing(temp_pdf_files, monkeypatch):
    """Verify that a task exceeding max retries is marked POISON and routed to DLQ."""
    manager = SecuroxiBulkManager()
    job = manager.create_batch_job([temp_pdf_files[0]], tenant_id="TENANT-DELTA")
    task = job.tasks[0]
    task.max_retries = 1

    def mock_scan_panic(path):
        raise RuntimeError("Simulated parser panic exception")

    monkeypatch.setattr(manager.scanner, "scan", mock_scan_panic)

    processed_task = manager.process_task(task)
    assert processed_task.status == TaskStatus.POISON
    assert processed_task.retry_count >= 1


def test_multi_tenant_job_isolation(temp_pdf_files):
    """Verify tenant isolation prevents unauthorized access to another tenant's batch job."""
    manager = SecuroxiBulkManager()
    job = manager.create_batch_job(temp_pdf_files, tenant_id="TENANT-SECRET")

    # Access with correct tenant_id
    assert manager.get_batch_job(job.batch_id, tenant_id="TENANT-SECRET") is not None

    # Access with wrong tenant_id: must return None
    assert manager.get_batch_job(job.batch_id, tenant_id="TENANT-OTHER") is None


def test_batch_api_endpoints(temp_pdf_files):
    """Verify FastAPI endpoints for batch status, retry, and cancellation."""
    manager = SecuroxiBulkManager()

    from securoxi.api.app import bulk_manager
    job = bulk_manager.create_batch_job(temp_pdf_files, tenant_id="TENANT-DEFAULT")

    # Fetch status
    res = client.get(f"/api/v1/batches/{job.batch_id}")
    assert res.status_code == 200
    assert res.json()["batch_id"] == job.batch_id

    # Cancel job
    cancel_res = client.post(f"/api/v1/batches/{job.batch_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["job"]["status"] == "CANCELLED"
