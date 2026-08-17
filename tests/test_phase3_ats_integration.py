"""
Unit Test Suite for SECUROXI Phase 3 Stage 5 — ATS Integration Framework.
Tests HMAC signature verification, idempotency deduplication, security-aware webhook ingestion,
malicious resume quarantine, and retry handling.
"""

import sys
import os
import json
import hmac
import hashlib
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.integrations.mock_ats import MockATSAdapter, ATSAuthenticationConfig
from securoxi.screening.eval_dataset import generate_phase2_evaluation_dataset, EVAL_FIXTURES_DIR


class TestPhase3ATSIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.auth_cfg = ATSAuthenticationConfig(
            provider_name="TEST_ATS_PROVIDER",
            api_key="test_key_12345",
            webhook_secret="test_secret_abc999"
        )
        cls.ats_adapter = MockATSAdapter(config=cls.auth_cfg)
        cls.dataset = generate_phase2_evaluation_dataset()
        cls.jd_path = os.path.join(EVAL_FIXTURES_DIR, "..", "phase2", "sample_jd.txt")

    def _generate_hmac_header(self, body_bytes: bytes) -> str:
        return hmac.new(
            self.auth_cfg.webhook_secret.encode("utf-8"),
            body_bytes,
            hashlib.sha256
        ).hexdigest()

    def test_1_invalid_hmac_signature_rejected(self):
        """Webhook with invalid HMAC signature header must be REJECTED immediately."""
        payload = {"event_id": "EVT-INVALID-SIG", "candidate_id": "C-001"}
        body_bytes = json.dumps(payload).encode("utf-8")

        res = self.ats_adapter.process_incoming_webhook(
            raw_body=body_bytes,
            signature_header="INVALID_SIG_HEADER",
            payload=payload,
            jd_source=self.jd_path
        )

        self.assertFalse(res.success)
        self.assertEqual(res.operation, "WEBHOOK_VERIFICATION")

    def test_2_clean_resume_webhook_processed(self):
        """Webhook with clean candidate resume must pass security gate and sync SAFE verdict to ATS."""
        clean_pdf = self.dataset[0]["filepath"]
        payload = {
            "event_id": "EVT-CLEAN-001",
            "event_type": "RESUME_ATTACHED",
            "candidate_id": "C-CLEAN-100",
            "file_path": clean_pdf
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        sig_header = self._generate_hmac_header(body_bytes)

        res = self.ats_adapter.process_incoming_webhook(
            raw_body=body_bytes,
            signature_header=sig_header,
            payload=payload,
            jd_source=self.jd_path
        )

        self.assertTrue(res.success)
        self.assertEqual(res.data["screening_result"]["security_verdict"], "SAFE")
        self.assertIn("C-CLEAN-100", self.ats_adapter.synced_results)

    def test_3_idempotency_duplicate_event_skipped(self):
        """Submitting duplicate webhook event ID must be skipped gracefully."""
        clean_pdf = self.dataset[0]["filepath"]
        payload = {
            "event_id": "EVT-CLEAN-001",  # Duplicate event_id from test_2!
            "event_type": "RESUME_ATTACHED",
            "candidate_id": "C-CLEAN-100",
            "file_path": clean_pdf
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        sig_header = self._generate_hmac_header(body_bytes)

        res = self.ats_adapter.process_incoming_webhook(
            raw_body=body_bytes,
            signature_header=sig_header,
            payload=payload,
            jd_source=self.jd_path
        )

        self.assertTrue(res.success)
        self.assertEqual(res.operation, "DEDUPLICATION")
        self.assertIn("Duplicate", res.message)

    def test_4_malicious_resume_webhook_quarantined(self):
        """Webhook with malicious prompt injection resume MUST be quarantined (HIGH_RISK). Security wins!"""
        malicious_pdf = self.dataset[4]["filepath"]  # candidate_malicious.pdf
        payload = {
            "event_id": "EVT-MALICIOUS-999",
            "event_type": "RESUME_ATTACHED",
            "candidate_id": "C-ATTACKER-999",
            "file_path": malicious_pdf
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        sig_header = self._generate_hmac_header(body_bytes)

        res = self.ats_adapter.process_incoming_webhook(
            raw_body=body_bytes,
            signature_header=sig_header,
            payload=payload,
            jd_source=self.jd_path
        )

        self.assertTrue(res.success)
        self.assertEqual(res.data["screening_result"]["security_verdict"], "HIGH_RISK")
        self.assertEqual(res.data["screening_result"]["screening_report"]["match_score"], 0.0)

    def test_5_retry_handler_success(self):
        """Retry handler must retry failed operations and return result when successful."""
        counter = {"attempts": 0}

        def flaky_func():
            counter["attempts"] += 1
            if counter["attempts"] < 2:
                raise ValueError("Transient network error")
            return "SUCCESS"

        out = self.ats_adapter.execute_with_retry(flaky_func, max_retries=3, delay_sec=0.01)
        self.assertEqual(out, "SUCCESS")
        self.assertEqual(counter["attempts"], 2)


if __name__ == "__main__":
    unittest.main()
