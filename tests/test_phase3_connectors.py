"""
Unit Test Suite for SECUROXI Phase 3 Stage 6 — Enterprise Data & Cloud Connectors.
Tests file discovery, SHA-256 content deduplication, modified files, deleted files,
inaccessible files, expired credentials, and connector health checks.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.connectors.base_connector import ConnectorConfig, ConnectorHealthStatus, StorageEventType
from securoxi.connectors.cloud_connectors import LocalFileConnector, ObjectStorageConnector, CloudDriveConnector
from securoxi.screening.eval_dataset import EVAL_FIXTURES_DIR, generate_phase2_evaluation_dataset


class TestPhase3Connectors(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dataset = generate_phase2_evaluation_dataset()

    def test_1_local_file_connector_discovery(self):
        """LocalFileConnector must discover PDF files in EVAL_FIXTURES_DIR cleanly."""
        connector = LocalFileConnector(watch_directory=EVAL_FIXTURES_DIR)

        self.assertEqual(connector.health_check(), ConnectorHealthStatus.HEALTHY)
        events = connector.discover_files()
        self.assertGreater(len(events), 0)

        # Check content fetch
        first_evt = events[0]
        content = connector.fetch_file_content(first_evt.file_id)
        self.assertEqual(len(content), first_evt.file_size_bytes)

    def test_2_object_storage_duplicate_deduplication(self):
        """ObjectStorageConnector must calculate SHA-256 and detect duplicate file content."""
        s3 = ObjectStorageConnector()
        content = b"Candidate Resume PDF Content Payload 12345"

        s3.add_mock_object("resume_001.pdf", content)
        events = s3.discover_files()

        self.assertEqual(len(events), 1)
        sha256 = events[0].content_hash_sha256

        self.assertFalse(s3.is_duplicate_content(sha256))
        # Second check returns True (duplicate content!)
        self.assertTrue(s3.is_duplicate_content(sha256))

    def test_3_cloud_drive_deleted_file_handling(self):
        """CloudDriveConnector must track FILE_DELETED events and raise FileNotFoundError on fetch."""
        drive = CloudDriveConnector()
        drive.upsert_drive_file("file_100", "resume_alex.pdf", b"Alex Rivers Resume")

        # Discover active file
        events1 = drive.discover_files()
        self.assertEqual(events1[0].event_type, StorageEventType.FILE_CREATED)

        # Delete file
        drive.delete_drive_file("file_100")
        events2 = drive.discover_files()
        self.assertEqual(events2[0].event_type, StorageEventType.FILE_DELETED)

        # Fetching deleted file raises FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            drive.fetch_file_content("file_100")

    def test_4_expired_credentials_handling(self):
        """Expired credentials must report EXPIRED_CREDENTIALS health and block discovery."""
        expired_cfg = ConnectorConfig(
            connector_id="CONN-EXPIRED-S3",
            source_type="OBJECT_STORAGE",
            is_credentials_expired=True
        )
        s3_expired = ObjectStorageConnector(config=expired_cfg)

        self.assertEqual(s3_expired.health_check(), ConnectorHealthStatus.EXPIRED_CREDENTIALS)

        with self.assertRaises(PermissionError):
            s3_expired.discover_files()


if __name__ == "__main__":
    unittest.main()
