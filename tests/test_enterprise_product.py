"""
End-to-End & Integration Test Suite for SECUROXI Stage 8 Enterprise Product Layer.
Tests REST API endpoints, ZIP bulk processing, audit logs, and API authentication.
"""

import sys
import os
import io
import zipfile
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.api.app import app, DEFAULT_API_KEY
from securoxi.storage.db import SecuroxiDatabase


class TestEnterpriseProductLayer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.headers = {"X-API-Key": DEFAULT_API_KEY}
        cls.db = SecuroxiDatabase()

    def test_1_get_dashboard_stats_endpoint(self):
        """GET /api/v1/stats must return summary counters."""
        response = self.client.get("/api/v1/stats", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_scans", data)
        self.assertIn("safe", data)
        self.assertIn("suspicious", data)
        self.assertIn("high_risk", data)

    def test_2_api_authentication_security_enforcement(self):
        """Requesting REST endpoints with invalid API key must return 401 Unauthorized."""
        response = self.client.get("/api/v1/stats", headers={"X-API-Key": "invalid_key_123"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid API Key or Bearer Token.")

    def test_3_single_pdf_upload_scan_end_to_end(self):
        """POST /api/v1/scan with clean resume PDF must return report JSON and save to database."""
        clean_pdf_path = os.path.abspath("tests/fixtures/clean_1_normal_resume.pdf")
        with open(clean_pdf_path, "rb") as f:
            response = self.client.post(
                "/api/v1/scan",
                headers=self.headers,
                files={"file": ("clean_1_normal_resume.pdf", f, "application/pdf")}
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["filename"], "clean_1_normal_resume.pdf")
        self.assertEqual(data["verdict"], "SAFE")
        self.assertIn("metadata", data)
        scan_id = data["metadata"]["scan_id"]

        # Fetch scan report by ID
        fetch_res = self.client.get(f"/api/v1/scan/{scan_id}", headers=self.headers)
        self.assertEqual(fetch_res.status_code, 200)
        self.assertEqual(fetch_res.json()["filename"], "clean_1_normal_resume.pdf")

    def test_4_zip_bulk_archive_upload_scan(self):
        """POST /api/v1/scan with ZIP archive containing multiple PDFs must extract and scan all documents."""
        clean_pdf_path = os.path.abspath("tests/fixtures/clean_1_normal_resume.pdf")
        malicious_pdf_path = os.path.abspath("tests/fixtures/malicious_resume.pdf")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            zip_file.write(clean_pdf_path, arcname="resume_clean.pdf")
            zip_file.write(malicious_pdf_path, arcname="resume_malicious.pdf")

        zip_buffer.seek(0)
        response = self.client.post(
            "/api/v1/scan",
            headers=self.headers,
            files={"file": ("bulk_batch.zip", zip_buffer, "application/zip")}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_files"], 2)
        self.assertEqual(data["high_risk"], 1)
        self.assertEqual(data["safe"], 1)

    def test_5_audit_logs_endpoint(self):
        """GET /api/v1/audit-logs must return historical operational security logs."""
        response = self.client.get("/api/v1/audit-logs", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        logs = response.json()
        self.assertIsInstance(logs, list)
        self.assertGreaterEqual(len(logs), 1)


if __name__ == "__main__":
    unittest.main()
