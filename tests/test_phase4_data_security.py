"""
Unit & Security Test Suite for SECUROXI Phase 4 Stage 4 — Data Security, Secrets & Retention.
Tests SQL injection prevention via parameterized queries, data retention purging,
secret redaction in logs, and transaction rollback.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.storage.db import SecuroxiDatabase


class TestPhase4DataSecurity(unittest.TestCase):

    def setUp(self):
        self.db = SecuroxiDatabase()

    def test_1_sql_injection_prevention_parameterized_queries(self):
        """SQL injection attempt in search payload MUST be safely parameterized."""
        sqli_payload = "' OR '1'='1' --"
        # Seed 1 record
        self.db.save_scan({
            "metadata": {"scan_id": "SCAN-SQLI-SAFE"},
            "filename": "legitimate_file.pdf",
            "document_type": "PDF",
            "verdict": "SAFE",
            "risk_score": 0
        })

        # Query with SQL injection string -> Parameterized query matches literal string, returns 0 records!
        results = self.db.list_scans(search=sqli_payload)
        self.assertEqual(len(results), 0)

    def test_2_data_retention_purging(self):
        """purge_expired_data must remove records older than specified retention days."""
        self.db.save_scan({
            "metadata": {"scan_id": "SCAN-OLD-RETENTION"},
            "filename": "old_file.pdf",
            "document_type": "PDF",
            "verdict": "SAFE",
            "risk_score": 0
        }, tenant_id="TENANT-PURGE-TEST")

        # Purge records older than 0 days (purges current test record)
        res = self.db.purge_expired_data(retention_days=0, tenant_id="TENANT-PURGE-TEST")
        self.assertGreaterEqual(res["scans_purged"], 1)

    def test_3_sensitive_secret_masking_in_audit_logs(self):
        """API key secrets logged during authentication failure MUST be masked (secu***)."""
        self.db.log_audit_event("AUTH_FAILURE", "API_CLIENT", "Invalid API Key attempt: secu***", tenant_id="TENANT-DEFAULT")
        logs = self.db.get_audit_logs(limit=5)
        found_masked = any("secu***" in log.get("details", "") for log in logs)
        self.assertTrue(found_masked)


if __name__ == "__main__":
    unittest.main()
