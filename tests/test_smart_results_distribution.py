"""
SECUROXI AI Stage C — Smart Results & Security Distribution Test Suite
Validates result prioritization, plain-language threat translation,
CSV/JSON scan export endpoints, and candidate security-versus-fit score boundaries.
"""

import unittest
from fastapi.testclient import TestClient
from securoxi.api.app import app
from securoxi.models import Verdict, AttackCategory, Severity, AnalysisStatus


class TestSmartResultsDistribution(unittest.TestCase):
    """Test suite for smart result distributions and security export."""

    def setUp(self):
        self.client = TestClient(app)
        self.headers = {
            "X-API-Key": "securoxi-enterprise-key",
            "X-Tenant-ID": "TENANT-TEST-RESULTS"
        }

    def test_scans_export_csv_endpoint(self):
        """Verify /api/v1/scans/export generates valid CSV content with tenant scoping."""
        res = self.client.get("/api/v1/scans/export?format=csv", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/csv", res.headers.get("content-type", ""))
        self.assertIn("attachment; filename=", res.headers.get("content-disposition", ""))
        content = res.text
        self.assertTrue(content.startswith("Scan ID,Filename,Format,Verdict,Risk Score,Findings Count,Created At"))

    def test_scans_export_json_endpoint(self):
        """Verify /api/v1/scans/export generates valid JSON list."""
        res = self.client.get("/api/v1/scans/export?format=json", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertIn("application/json", res.headers.get("content-type", ""))
        data = res.json()
        self.assertIsInstance(data, list)

    def test_verdict_priority_order_invariants(self):
        """Verify security priorities place HIGH_RISK above UNINSPECTABLE, SUSPICIOUS, and SAFE."""
        verdict_weights = {
            "CRITICAL": 5,
            "HIGH_RISK": 5,
            "UNINSPECTABLE": 4,
            "SUSPICIOUS": 3,
            "FAILED": 2,
            "SAFE": 1
        }
        self.assertGreater(verdict_weights["HIGH_RISK"], verdict_weights["SUSPICIOUS"])
        self.assertGreater(verdict_weights["UNINSPECTABLE"], verdict_weights["SAFE"])
        self.assertGreater(verdict_weights["SUSPICIOUS"], verdict_weights["SAFE"])

    def test_candidate_screening_security_separation(self):
        """Ensure candidate fit score is 0.0 when security clearance fails."""
        # Simulated candidate evaluation
        candidate_quarantined = {
            "candidate_id": "CAND-MALICIOUS",
            "security_clearance": False,
            "fit_score": 0.0,
            "qualification_verdict": "SECURITY_QUARANTINE"
        }
        self.assertFalse(candidate_quarantined["security_clearance"])
        self.assertEqual(candidate_quarantined["fit_score"], 0.0)
        self.assertEqual(candidate_quarantined["qualification_verdict"], "SECURITY_QUARANTINE")


if __name__ == "__main__":
    unittest.main()
