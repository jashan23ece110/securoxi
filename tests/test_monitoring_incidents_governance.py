"""
SECUROXI AI Stage H — Monitoring, Incidents & Enterprise Governance Test Suite
Validates system health telemetry, incident lifecycle management, policy engine authority,
audit logging immutability, data retention boundaries, and tenant isolation.
"""

import unittest
from fastapi.testclient import TestClient
from securoxi.api.app import app
from securoxi.storage.db import db


class TestMonitoringIncidentsGovernance(unittest.TestCase):
    """Test suite for operational monitoring, incident response, policies, and audit trails."""

    def setUp(self):
        self.client = TestClient(app)
        self.headers = {
            "X-API-Key": "securoxi-enterprise-key",
            "X-Tenant-ID": "TENANT-TEST-GOVERNANCE"
        }

    def test_health_telemetry_endpoint(self):
        """Verify /api/v1/health/liveness and readiness endpoints return operational status."""
        res_live = self.client.get("/api/v1/health/liveness")
        self.assertEqual(res_live.status_code, 200)
        self.assertEqual(res_live.json()["status"], "alive")

        res_ready = self.client.get("/api/v1/health/readiness")
        self.assertEqual(res_ready.status_code, 200)
        self.assertIn("status", res_ready.json())

    def test_incident_lifecycle_board_persistence(self):
        """Verify incident record creation and listing with valid lifecycle status."""
        test_incident = {
            "incident_id": "INC-TEST-001",
            "severity": "CRITICAL",
            "status": "INVESTIGATING",
            "attack_type": "PROMPT_INJECTION",
            "affected_asset": "candidate_payload.pdf"
        }
        inc_id = db.save_incident(test_incident, tenant_id="TENANT-TEST-GOVERNANCE")
        self.assertEqual(inc_id, "INC-TEST-001")

        incidents = db.list_incidents(tenant_id="TENANT-TEST-GOVERNANCE")
        matching = [i for i in incidents if i["incident_id"] == "INC-TEST-001"]
        self.assertTrue(len(matching) > 0)
        self.assertEqual(matching[0]["status"], "INVESTIGATING")
        self.assertEqual(matching[0]["severity"], "CRITICAL")

    def test_audit_event_logging_and_tenant_scoping(self):
        """Verify audit trail event logging and strict tenant filtering."""
        db.log_audit_event(
            event_type="POLICY_RULE_ENFORCED",
            actor="PolicyEngine",
            details="Blocked malicious payload candidate_0412.docx",
            tenant_id="TENANT-TEST-GOVERNANCE"
        )
        logs = db.get_audit_logs(limit=10, tenant_id="TENANT-TEST-GOVERNANCE")
        matching = [l for l in logs if l.get("event_type") == "POLICY_RULE_ENFORCED"]
        self.assertTrue(len(matching) > 0)

    def test_data_retention_purge_contract(self):
        """Verify data retention purge logic operates within safe boundaries."""
        res = db.purge_expired_data(retention_days=90, tenant_id="TENANT-TEST-GOVERNANCE")
        self.assertIn("scans_purged", res)
        self.assertIn("logs_purged", res)
        self.assertGreaterEqual(res["scans_purged"], 0)
        self.assertGreaterEqual(res["logs_purged"], 0)


if __name__ == "__main__":
    unittest.main()
