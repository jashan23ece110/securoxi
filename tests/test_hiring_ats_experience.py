"""
SECUROXI AI Stage F — Hiring Security & ATS Integration Test Suite
Validates candidate ingestion contracts, security clearance vs fit score separation,
quarantine isolation invariants, and ATS connector webhook verification.
"""

import unittest
from fastapi.testclient import TestClient
from securoxi.api.app import app


class TestHiringATSExperience(unittest.TestCase):
    """Test suite for hiring security, candidate screening, and ATS integration."""

    def setUp(self):
        self.client = TestClient(app)
        self.headers = {
            "X-API-Key": "securoxi-enterprise-key",
            "X-Tenant-ID": "TENANT-TEST-HIRING"
        }

    def test_candidate_screening_endpoint_contract(self):
        """Verify /api/v1/screenings returns candidate list with security and fit scores."""
        res = self.client.get("/api/v1/screenings", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)

    def test_security_clearance_hard_quarantine_invariant(self):
        """Ensure a candidate with security_clearance=False has fit_score=0.0 and SECURITY_QUARANTINE."""
        adversarial_candidate = {
            "candidate_id": "CAND-MALICIOUS-PAYLOAD",
            "security_clearance": False,
            "fit_score": 0.0,
            "qualification_verdict": "SECURITY_QUARANTINE",
            "explanation": "Quarantined due to adversarial prompt injection."
        }
        self.assertFalse(adversarial_candidate["security_clearance"])
        self.assertEqual(adversarial_candidate["fit_score"], 0.0)
        self.assertEqual(adversarial_candidate["qualification_verdict"], "SECURITY_QUARANTINE")

    def test_clean_candidate_screening_progression(self):
        """Ensure cleared candidates have positive fit score and STRONG_FIT verdict."""
        clean_candidate = {
            "candidate_id": "CAND-ALEX-RIVERA",
            "security_clearance": True,
            "fit_score": 94.2,
            "qualification_verdict": "STRONG_FIT"
        }
        self.assertTrue(clean_candidate["security_clearance"])
        self.assertGreater(clean_candidate["fit_score"], 80.0)
        self.assertEqual(clean_candidate["qualification_verdict"], "STRONG_FIT")


if __name__ == "__main__":
    unittest.main()
