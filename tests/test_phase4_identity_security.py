"""
Unit & Integration Security Test Suite for SECUROXI Phase 4 Stage 2 — Identity, Auth & Multi-Tenant Security Hardening.
Tests unauthenticated rejection, production key enforcement, cross-tenant IDOR isolation,
audit log isolation, RBAC role permissions, and object ID guessing rejection.
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.api.app import app, db, control_plane
from securoxi.control_plane.governance import UserRole, ControlPlanePermission


class TestPhase4IdentitySecurity(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        # Create 2 isolated tenants
        self.tenant_a = control_plane.create_tenant("Tenant Alpha", retention_days=90)
        self.tenant_b = control_plane.create_tenant("Tenant Beta", retention_days=30)

        # Generate API keys for tenants
        self.raw_key_a, _ = control_plane.create_api_key(self.tenant_a.tenant_id, UserRole.SUPER_ADMIN)
        self.raw_key_b, _ = control_plane.create_api_key(self.tenant_b.tenant_id, UserRole.SUPER_ADMIN)
        self.recruiter_key_a, _ = control_plane.create_api_key(self.tenant_a.tenant_id, UserRole.RECRUITER)

    def test_1_invalid_api_key_unauthorized(self):
        """Invalid API key must be rejected with 401 Unauthorized."""
        res = self.client.get("/api/v1/stats", headers={"X-API-Key": "INVALID-KEY-12345"})
        self.assertEqual(res.status_code, 401)
        self.assertIn("Invalid API Key", res.json()["detail"])

    def test_2_cross_tenant_idor_scan_report_isolation(self):
        """Tenant B attempting to query Tenant A scan ID MUST be rejected with 404 (IDOR Blocked)."""
        scan_id = db.save_scan({
            "metadata": {"scan_id": "SCAN-ALPHA-1001"},
            "filename": "secret_doc_a.pdf",
            "document_type": "PDF",
            "verdict": "SAFE",
            "risk_score": 0
        }, tenant_id=self.tenant_a.tenant_id)

        # Tenant A request -> Allowed (200)
        res_a = self.client.get(f"/api/v1/scan/{scan_id}", headers={"X-API-Key": self.raw_key_a})
        self.assertEqual(res_a.status_code, 200)
        self.assertEqual(res_a.json()["filename"], "secret_doc_a.pdf")

        # Tenant B request -> Blocked / Isolated (404)
        res_b = self.client.get(f"/api/v1/scan/{scan_id}", headers={"X-API-Key": self.raw_key_b})
        self.assertEqual(res_b.status_code, 404)

    def test_3_cross_tenant_audit_log_isolation(self):
        """Tenant B fetching audit logs MUST NOT see Tenant A's audit logs."""
        db.log_audit_event("SENSITIVE_ACTION", "UserAlpha", "Tenant A secret activity", tenant_id=self.tenant_a.tenant_id)

        # Tenant B queries audit logs -> Does NOT see Tenant A logs!
        res_b = self.client.get("/api/v1/audit-logs", headers={"X-API-Key": self.raw_key_b})
        self.assertEqual(res_b.status_code, 200)
        logs_b = res_b.json()
        for log in logs_b:
            self.assertNotIn("Tenant A secret activity", log.get("details", ""))

    def test_4_rbac_permission_check(self):
        """RECRUITER role checking control plane permission check."""
        allowed, msg, role = control_plane.check_permission(self.recruiter_key_a, ControlPlanePermission.MANAGE_POLICY)
        self.assertFalse(allowed)
        self.assertIn("FORBIDDEN", msg)

    def test_5_object_id_guessing_rejection(self):
        """Random non-existent scan ID returns 404 Not Found."""
        res = self.client.get("/api/v1/scan/SCAN-NONEXISTENT-9999", headers={"X-API-Key": self.raw_key_a})
        self.assertEqual(res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
