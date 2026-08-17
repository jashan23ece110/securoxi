"""
Unit Test Suite for SECUROXI Phase 3 Stage 8 — Automated Response & Incident Management.
Tests incident creation, policy authorization controls, deduplication, escalation,
and full 6-state lifecycle transitions.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.brain.incident_management import IncidentManager, IncidentState, ResponseActionType


class TestPhase3IncidentResponse(unittest.TestCase):

    def setUp(self):
        self.mgr = IncidentManager()

    def test_1_automatic_block_incident(self):
        """High risk threat context must generate incident with BLOCK response authorized by Policy Engine."""
        inc = self.mgr.create_incident(
            source="S3_CONNECTOR",
            affected_asset="malicious_resume.pdf",
            attack_type="PROMPT_INJECTION",
            risk_score=100.0,
            evidence="White text prompt injection detected"
        )

        self.assertEqual(inc.state, IncidentState.DETECTED)
        self.assertEqual(inc.severity, "CRITICAL")
        self.assertIn(ResponseActionType.BLOCK.value, inc.response_actions)
        self.assertEqual(inc.policy_decision["action"], "BLOCK")

    def test_2_manual_review_incident(self):
        """Suspicious threat context must generate incident with manual review response actions."""
        inc = self.mgr.create_incident(
            source="ATS_WEBHOOK",
            affected_asset="suspicious_formatting.pdf",
            attack_type="UNUSUAL_FORMATTING",
            risk_score=40.0,
            evidence="Unusual font ratio"
        )

        self.assertEqual(inc.state, IncidentState.DETECTED)
        self.assertIn(ResponseActionType.MARK_CANDIDATE_MANUAL_REVIEW.value, inc.response_actions)

    def test_3_policy_authorization_over_llm_recommendation(self):
        """Policy Engine MUST dictate response action, even if LLM recommends ALLOW."""
        inc = self.mgr.create_incident(
            source="AGENT_RUNTIME",
            affected_asset="doc_attack.pdf",
            attack_type="PROMPT_INJECTION",
            risk_score=95.0,
            evidence="Instruction override",
            llm_recommendation="LLM suggests ALLOW"
        )

        # Policy Engine BLOCK overrides LLM recommendation!
        self.assertIn(ResponseActionType.BLOCK.value, inc.response_actions)
        self.assertEqual(inc.policy_decision["action"], "BLOCK")
        # LLM recommendation is logged in audit trail only
        audit_text = str(inc.audit_trail)
        self.assertIn("LLM suggested", audit_text)

    def test_4_deduplication_and_escalation(self):
        """Duplicate incident creation must deduplicate and escalate severity if risk score increases."""
        inc1 = self.mgr.create_incident(
            source="S3",
            affected_asset="candidate_john.pdf",
            attack_type="ATS_MANIPULATION",
            risk_score=75.0,
            evidence="Keyword stuffing"
        )

        inc_id1 = inc1.incident_id

        # Re-submit duplicate with higher risk score (95.0)
        inc2 = self.mgr.create_incident(
            source="S3",
            affected_asset="candidate_john.pdf",
            attack_type="ATS_MANIPULATION",
            risk_score=95.0,
            evidence="Updated threat detection"
        )

        # Verification: Deduplicated to same incident ID, escalated to CRITICAL!
        self.assertEqual(inc2.incident_id, inc_id1)
        self.assertEqual(inc2.severity, "CRITICAL")
        self.assertEqual(inc2.risk_score, 95.0)

    def test_5_full_incident_lifecycle_transitions(self):
        """Incident must transition through full 6-state lifecycle cleanly."""
        inc = self.mgr.create_incident(
            source="API_UPLOAD",
            affected_asset="resume_test.pdf",
            attack_type="PROMPT_INJECTION",
            risk_score=85.0,
            evidence="Prompt injection"
        )

        self.assertEqual(inc.state, IncidentState.DETECTED)

        # Assign -> INVESTIGATING
        self.mgr.assign_incident(inc.incident_id, assignee="SecurityAnalystSarah")
        self.assertEqual(inc.state, IncidentState.INVESTIGATING)
        self.assertEqual(inc.assigned_to, "SecurityAnalystSarah")

        # Resolve -> RESOLVED
        self.mgr.resolve_incident(inc.incident_id, resolution_notes="Quarantined candidate PDF; verified threat contained.")
        self.assertEqual(inc.state, IncidentState.RESOLVED)

        # Close -> CLOSED
        self.mgr.close_incident(inc.incident_id)
        self.assertEqual(inc.state, IncidentState.CLOSED)
        self.assertGreater(len(inc.audit_trail), 3)


if __name__ == "__main__":
    unittest.main()
