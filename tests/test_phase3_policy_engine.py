"""
Unit Test Suite for SECUROXI Phase 3 Stage 4 — Enterprise Security Policy Engine.
Tests priority ordering, conflict resolution, default fallbacks, unknown conditions,
explanation auditability, and fail-safe error handling.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.brain.policy_engine import (
    SecuroxiPolicyEngine, PolicyContext, PolicyRule, PolicyDecisionAction
)


class TestPhase3PolicyEngine(unittest.TestCase):

    def setUp(self):
        self.engine = SecuroxiPolicyEngine()

    def test_1_safe_document_allowed(self):
        """Safe context must trigger ALLOW decision."""
        ctx = PolicyContext(
            verdict="SAFE",
            risk_score=0.0,
            source="RESUME_UPLOAD",
            target="CANDIDATE_SCREENING"
        )
        dec = self.engine.evaluate_policy(ctx)

        self.assertEqual(dec.action, PolicyDecisionAction.ALLOW)
        self.assertEqual(dec.rule_id, "RULE-010-SAFE-ALLOW")

    def test_2_high_risk_document_blocked(self):
        """High risk context must trigger BLOCK decision via high priority rule."""
        ctx = PolicyContext(
            verdict="HIGH_RISK",
            risk_score=100.0,
            source="RESUME_UPLOAD",
            target="ATS_DATABASE",
            threat_types=["PROMPT_INJECTION"]
        )
        dec = self.engine.evaluate_policy(ctx)

        self.assertEqual(dec.action, PolicyDecisionAction.BLOCK)
        self.assertEqual(dec.rule_id, "RULE-100-HIGH-RISK-BLOCK")
        self.assertEqual(dec.rule_priority, 100)

    def test_3_rule_priority_conflict_resolution(self):
        """Higher priority rule (Priority 200) MUST override lower priority rule (Priority 10)."""
        custom_rule = PolicyRule(
            rule_id="RULE-200-OVERRIDE-BLOCK",
            priority=200,
            name="Super High Priority Custom Block",
            description="Overrides all lower priority rules.",
            action=PolicyDecisionAction.BLOCK,
            condition=lambda c: True  # Matches everything!
        )
        self.engine.register_rule(custom_rule)

        ctx = PolicyContext(
            verdict="SAFE",
            risk_score=0.0,
            source="RESUME_UPLOAD",
            target="CANDIDATE_SCREENING"
        )
        dec = self.engine.evaluate_policy(ctx)

        # Priority 200 rule MUST win over Priority 10 ALLOW rule!
        self.assertEqual(dec.action, PolicyDecisionAction.BLOCK)
        self.assertEqual(dec.rule_id, "RULE-200-OVERRIDE-BLOCK")

    def test_4_unknown_condition_default_failsafe(self):
        """Context matching no rules must trigger default fail-safe QUARANTINE."""
        empty_engine = SecuroxiPolicyEngine()
        empty_engine.rules = []  # Clear default rules

        ctx = PolicyContext(
            verdict="UNKNOWN_VERDICT",
            risk_score=15.0,
            source="UNKNOWN_SOURCE",
            target="UNKNOWN_TARGET"
        )
        dec = empty_engine.evaluate_policy(ctx)

        self.assertEqual(dec.action, PolicyDecisionAction.QUARANTINE)
        self.assertEqual(dec.rule_id, "DEFAULT_FALLBACK_NO_MATCH")

    def test_5_exception_handling_failsafe(self):
        """Rule throwing an exception during evaluation must trigger Emergency Fail-Safe BLOCK."""
        broken_rule = PolicyRule(
            rule_id="RULE-999-BROKEN",
            priority=999,
            name="Broken Exception Rule",
            description="Throws exception",
            action=PolicyDecisionAction.ALLOW,
            condition=lambda c: 1 / 0  # ZeroDivisionError!
        )
        self.engine.register_rule(broken_rule)

        ctx = PolicyContext(verdict="SAFE", risk_score=0.0, source="TEST", target="TEST")
        dec = self.engine.evaluate_policy(ctx)

        # Fail-safe mechanism catches exception and enforces BLOCK!
        self.assertEqual(dec.action, PolicyDecisionAction.BLOCK)


if __name__ == "__main__":
    unittest.main()
