"""
Unit test wrapper for SECUROXI evaluation suite.
Ensures python -m unittest discover tests executes evaluation framework.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.evaluate import run_evaluation


class TestEvaluationSuite(unittest.TestCase):

    def test_run_full_evaluation_suite(self):
        """Run complete 50-document evaluation suite and verify accuracy thresholds."""
        summary = run_evaluation()
        self.assertGreaterEqual(summary["total_documents"], 50)
        self.assertGreaterEqual(summary["accuracy"], 70.0)
        self.assertGreaterEqual(summary["precision"], 90.0)
        self.assertGreaterEqual(summary["recall"], 60.0)


if __name__ == "__main__":
    unittest.main()
