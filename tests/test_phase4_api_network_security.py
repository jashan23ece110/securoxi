"""
Unit & Security Test Suite for SECUROXI Phase 4 Stage 3 — API & Network Security Hardening.
Tests SSRF private IP blocking, AWS Metadata IMDS protection, scheme validation,
secure HTTP response headers, and ATS webhook signature security.
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.api.app import app
from securoxi.network_security import SecuroxiSSRFGuard
from securoxi.integrations.mock_ats import MockATSAdapter


class TestPhase4APINetworkSecurity(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.ats = MockATSAdapter()

    def test_1_ssrf_private_ip_blocking(self):
        """Outbound URL validator MUST block private/loopback IP addresses."""
        blocked_urls = [
            "http://127.0.0.1/admin",
            "http://10.0.0.5/internal-api",
            "http://192.168.1.100/router",
            "http://172.16.0.1/db"
        ]

        for url in blocked_urls:
            is_safe, reason = SecuroxiSSRFGuard.validate_url(url)
            self.assertFalse(is_safe, f"Failed to block private IP: {url}")
            self.assertIn("SSRF_BLOCKED", reason)

    def test_2_ssrf_aws_metadata_imds_protection(self):
        """Outbound URL validator MUST block AWS Cloud Metadata IMDS IP 169.254.169.254."""
        imds_url = "http://169.254.169.254/latest/meta-data/iam/security-credentials/"
        is_safe, reason = SecuroxiSSRFGuard.validate_url(imds_url)
        self.assertFalse(is_safe)
        self.assertIn("SSRF_BLOCKED", reason)

    def test_3_ssrf_invalid_scheme_blocking(self):
        """Outbound URL validator MUST reject non-HTTP(S) schemes such as file://, gopher://, ftp://."""
        invalid_urls = [
            "file:///etc/passwd",
            "gopher://malicious.internal:70/",
            "ftp://files.internal/secret.key"
        ]

        for url in invalid_urls:
            is_safe, reason = SecuroxiSSRFGuard.validate_url(url)
            self.assertFalse(is_safe)
            self.assertIn("BLOCKED_SCHEME", reason)

    def test_4_valid_external_url_allowed(self):
        """Legitimate external public HTTPS URLs must be approved."""
        safe_url = "https://api.github.com/webhooks"
        is_safe, reason = SecuroxiSSRFGuard.validate_url(safe_url)
        self.assertTrue(is_safe)
        self.assertEqual(reason, "URL_SAFE")

    def test_5_secure_http_response_headers(self):
        """REST API responses MUST return secure HTTP headers (nosniff, DENY, HSTS)."""
        res = self.client.get("/api/v1/stats")
        self.assertEqual(res.status_code, 200)

        headers = res.headers
        self.assertEqual(headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(headers.get("x-frame-options"), "DENY")
        self.assertEqual(headers.get("x-xss-protection"), "1; mode=block")
        self.assertIn("max-age=31536000", headers.get("strict-transport-security", ""))

    def test_6_webhook_signature_forgery_rejection(self):
        """Webhook event with forged/invalid HMAC signature MUST be rejected."""
        payload_bytes = b'{"event": "RESUME_ATTACHED"}'
        forged_sig = "invalid_signature_hash_999"

        res = self.ats.process_incoming_webhook(payload_bytes, forged_sig, {"event": "RESUME_ATTACHED"}, "jd.txt")
        self.assertFalse(res.success)
        self.assertIn("Invalid HMAC signature", res.message)


if __name__ == "__main__":
    unittest.main()
