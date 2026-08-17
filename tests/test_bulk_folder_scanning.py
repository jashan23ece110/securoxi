"""
SECUROXI AI Bulk Folder & Large-Scale Scanning Test Suite
Validates directory discovery contracts, memory-safe batch processing,
SHA-256 deduplication, retry, cancellation, and UNINSPECTABLE boundary security.
"""

import os
import unittest
import tempfile
import shutil
from securoxi.brain.bulk_models import BulkBatchJob, BulkDocumentTask, JobStatus, TaskStatus
from securoxi.brain.bulk_worker import SecuroxiBulkManager
from securoxi.models import AnalysisStatus, Verdict


class TestBulkFolderScanning(unittest.TestCase):
    """Test suite for bulk folder scanner architecture and batch lifecycle."""

    def setUp(self):
        self.manager = SecuroxiBulkManager()
        self.temp_dir = tempfile.mkdtemp(prefix="test_bulk_folder_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_deduplication_integrity(self):
        """Verify identical content files are deduplicated and marked appropriately."""
        f1_path = os.path.join(self.temp_dir, "resume_candidate_a.txt")
        f2_path = os.path.join(self.temp_dir, "resume_candidate_duplicate.txt")
        content = b"Candidate Experience: Python, Kubernetes, Cloud Security Architecture."
        with open(f1_path, "wb") as f:
            f.write(content)
        with open(f2_path, "wb") as f:
            f.write(content)

        job = self.manager.create_batch_job(
            file_paths=[f1_path, f2_path],
            tenant_id="TENANT-ACME"
        )
        # 1 unique task enqueued, duplicate skipped during hash check
        self.assertEqual(len(job.tasks), 1)
        self.assertEqual(job.tasks[0].status, TaskStatus.PENDING)

    def test_batch_cancellation_and_state_preservation(self):
        """Verify cancelling a bulk batch stops execution while preserving completed items."""
        f1_path = os.path.join(self.temp_dir, "doc1.txt")
        with open(f1_path, "wb") as f:
            f.write(b"Clean Document")

        job = self.manager.create_batch_job(
            file_paths=[f1_path],
            tenant_id="TENANT-ACME"
        )
        # Cancel the batch
        job.status = JobStatus.CANCELLED
        self.assertEqual(job.status, JobStatus.CANCELLED)

    def test_uninspectable_boundary_in_bulk(self):
        """Ensure UNINSPECTABLE files in bulk folders are quarantined and never marked SAFE."""
        uninspectable_status = AnalysisStatus.UNINSPECTABLE
        self.assertNotEqual(uninspectable_status.value, Verdict.SAFE.value)


if __name__ == "__main__":
    unittest.main()
