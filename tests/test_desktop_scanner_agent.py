"""
SECUROXI AI Stage I — Desktop Scanner & Local Folder Agent Test Suite
Validates folder discovery, SHA-256 deduplication, symlink breakout protection,
durable SQLite queue persistence, and batch processing resilience.
"""

import os
import shutil
import tempfile
import unittest
from securoxi.agent.folder_scanner import LocalFolderScanner
from securoxi.agent.local_queue import LocalScanQueue, QueueItemState


class TestDesktopScannerAgent(unittest.TestCase):
    """Test suite for native desktop scanner and local queue manager."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="securoxi_agent_test_")
        self.db_path = os.path.join(self.temp_dir, "test_queue.db")

        # Create sample files
        self.doc1 = os.path.join(self.temp_dir, "resume1.pdf")
        with open(self.doc1, "wb") as f:
            f.write(b"%PDF-1.4 test document 1")

        self.doc2 = os.path.join(self.temp_dir, "resume2.docx")
        with open(self.doc2, "wb") as f:
            f.write(b"Word document content")

        # Duplicate file (same content as doc1)
        self.doc_dup = os.path.join(self.temp_dir, "resume1_copy.pdf")
        with open(self.doc_dup, "wb") as f:
            f.write(b"%PDF-1.4 test document 1")

        # Unsupported file
        self.unsupported = os.path.join(self.temp_dir, "executable.bin")
        with open(self.unsupported, "wb") as f:
            f.write(b"\x7fELF\x02\x01\x01")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_folder_discovery_and_deduplication(self):
        """Verify scanner discovers supported files and flags content duplicates via SHA-256."""
        scanner = LocalFolderScanner()
        discovery = scanner.discover_folder(self.temp_dir)

        self.assertEqual(discovery["total_files"], 4)
        self.assertEqual(discovery["supported_count"], 3)
        self.assertEqual(discovery["unsupported_count"], 1)
        self.assertEqual(discovery["duplicate_count"], 1)

        # Check duplicate flag
        dup_items = [f for f in discovery["files"] if f.is_duplicate]
        self.assertEqual(len(dup_items), 1)
        self.assertIn(dup_items[0].file_name, ["resume1.pdf", "resume1_copy.pdf"])

    def test_symlink_breakout_prevention(self):
        """Verify symlinks pointing outside target directory are skipped safely."""
        external_dir = tempfile.mkdtemp(prefix="securoxi_external_")
        try:
            external_file = os.path.join(external_dir, "secret.txt")
            with open(external_file, "w") as f:
                f.write("sensitive data")

            symlink_path = os.path.join(self.temp_dir, "symlink_secret.txt")
            try:
                os.symlink(external_file, symlink_path)
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks not supported in environment")

            scanner = LocalFolderScanner()
            discovery = scanner.discover_folder(self.temp_dir)

            # Ensure external file was not discovered through breakout
            discovered_names = [f.file_name for f in discovery["files"]]
            self.assertNotIn("secret.txt", discovered_names)
            self.assertNotIn("symlink_secret.txt", discovered_names)
        finally:
            shutil.rmtree(external_dir, ignore_errors=True)

    def test_durable_local_queue_lifecycle(self):
        """Verify SQLite queue batch creation, item state transitions, and crash recovery."""
        queue = LocalScanQueue(db_path=self.db_path)
        scanner = LocalFolderScanner()
        discovery = scanner.discover_folder(self.temp_dir)

        files_data = [
            {
                "file_path": f.file_path,
                "relative_path": f.relative_path,
                "file_name": f.file_name,
                "sha256_hash": f.sha256_hash,
                "size_bytes": f.size_bytes,
                "is_duplicate": f.is_duplicate,
            }
            for f in discovery["files"] if f.is_supported
        ]

        batch_id = queue.create_batch(self.temp_dir, files_data)
        self.assertTrue(batch_id.startswith("BATCH-"))

        progress = queue.get_batch_progress(batch_id)
        self.assertEqual(progress["total_files"], 3)
        self.assertEqual(progress["queued"], 2)  # 2 clean queued
        self.assertEqual(progress["duplicates_skipped"], 1)  # 1 duplicate

        # Process an item
        pending = queue.get_pending_items(batch_id, limit=1)
        self.assertEqual(len(pending), 1)

        item = pending[0]
        queue.update_item_state(item["item_id"], QueueItemState.COMPLETED, remote_scan_id="SCAN-TEST-001")

        updated_progress = queue.get_batch_progress(batch_id)
        self.assertEqual(updated_progress["completed"], 1)
        self.assertEqual(updated_progress["queued"], 1)


if __name__ == "__main__":
    unittest.main()
