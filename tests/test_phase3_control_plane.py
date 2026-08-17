"""
Unit Test Suite for SECUROXI Phase 3 Stage 9 — Enterprise Control Plane, Governance & Observability.
Tests tenant creation & isolation, RBAC role permission checks, unauthorized access rejection,
API key controls, data retention configuration, and system metrics.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.control_plane.governance import (
    EnterpriseControlPlane, UserRole, ControlPlanePermission
)


class TestPhase3ControlPlane(unittest.TestCase):

    def setUp(self):
        self.cp = EnterpriseControlPlane()
        self.tenant = self.cp.create_tenant("Acme Corp", retention_days=60)

    def test_1_tenant_creation_and_retention(self):
        """Tenant creation must set tenant_id and custom data retention days."""
        self.assertIn(self.tenant.tenant_id, self.cp.tenants)
        self.assertEqual(self.tenant.retention_days, 60)
        self.assertTrue(self.tenant.is_active)

    def test_2_super_admin_rbac_permissions(self):
        """SUPER_ADMIN role must be allowed for all control plane permissions."""
        raw_key, rec = self.cp.create_api_key(self.tenant.tenant_id, UserRole.SUPER_ADMIN)

        allowed, msg, role = self.cp.check_permission(raw_key, ControlPlanePermission.MANAGE_TENANTS)
        self.assertTrue(allowed)
        self.assertEqual(role, UserRole.SUPER_ADMIN)

    def test_3_recruiter_forbidden_on_admin_permission(self):
        """RECRUITER role attempting MANAGE_POLICY must be rejected with FORBIDDEN."""
        raw_key, rec = self.cp.create_api_key(self.tenant.tenant_id, UserRole.RECRUITER)

        allowed, msg, role = self.cp.check_permission(raw_key, ControlPlanePermission.MANAGE_POLICY)
        self.assertFalse(allowed)
        self.assertIn("FORBIDDEN", msg)

    def test_4_invalid_api_key_unauthorized(self):
        """Invalid API key string must be rejected immediately with UNAUTHORIZED."""
        allowed, msg, role = self.cp.check_permission("INVALID_KEY_9999", ControlPlanePermission.READ_SCAN)
        self.assertFalse(allowed)
        self.assertIn("UNAUTHORIZED", msg)

    def test_5_observability_metrics_collection(self):
        """System metrics must record scan volume, threats, latency, and detection rate."""
        self.cp.record_scan_metrics(latency_ms=10.0, has_threat=False)
        self.cp.record_scan_metrics(latency_ms=20.0, has_threat=True)

        metrics = self.cp.get_system_metrics()
        self.assertEqual(metrics["total_scans_processed"], 2)
        self.assertEqual(metrics["threats_detected"], 1)
        self.assertEqual(metrics["detection_rate_pct"], 50.0)
        self.assertEqual(metrics["average_scan_latency_ms"], 15.0)


if __name__ == "__main__":
    unittest.main()
