"""
Unit Test Suite for SECUROXI Phase 2 Stage 9 — Evaluation, Accuracy & Bias Testing.
Verifies evaluation metrics, precision, recall, F1, security gate accuracy, and irrelevance/bias robustness.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.screening.evaluate_screening import run_phase2_screening_evaluation


class TestPhase2EvaluationSuite(unittest.TestCase):

    def test_phase2_evaluation_benchmark_metrics(self):
        """Executes Phase 2 benchmark evaluation and verifies precision, recall, F1, security gate accuracy, and bias robustness."""
        metrics = run_phase2_screening_evaluation()

        self.assertGreaterEqual(metrics["precision"], 90.0)
        self.assertGreaterEqual(metrics["recall"], 90.0)
        self.assertGreaterEqual(metrics["f1"], 90.0)
        self.assertEqual(metrics["security_gate_accuracy"], 100.0)
        # Verify irrelevance / bias robustness: adding hobbies must cause 0.0 score fluctuation!
        self.assertEqual(metrics["bias_score_delta"], 0.0)


if __name__ == "__main__":
    unittest.main()
