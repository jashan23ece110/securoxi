"""
Unit Test Suite for SECUROXI Phase 2 Stage 10 — Productionization & Final Validation.
Tests screening performance benchmarks, ranking stability & reproducibility, and input validation.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.config import SecuroxiConfig
from securoxi.screening.benchmark_screening import run_screening_benchmarks
from securoxi.screening.pipeline import SecuroxiScreeningPipeline
from securoxi.screening.eval_dataset import generate_phase2_evaluation_dataset, EVAL_FIXTURES_DIR


class TestPhase2Production(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = SecuroxiConfig()
        cls.pipeline = SecuroxiScreeningPipeline(config=cls.config)
        cls.dataset = generate_phase2_evaluation_dataset()
        cls.jd_path = os.path.join(EVAL_FIXTURES_DIR, "..", "phase2", "sample_jd.txt")

    def test_1_screening_performance_benchmarks(self):
        """Screening performance benchmarks must execute and return valid latency and memory metrics."""
        bench = run_screening_benchmarks()

        self.assertGreater(bench["single_resume_latency_ms"], 0.0)
        self.assertGreater(bench["batch_5_ranking_latency_ms"], 0.0)
        self.assertGreater(bench["throughput_resumes_per_sec"], 0.0)
        self.assertGreater(bench["peak_memory_mb"], 0.0)

    def test_2_ranking_stability_and_reproducibility(self):
        """Running multi-candidate ranking 3 consecutive times must yield IDENTICAL candidate order (100% deterministic)."""
        paths = [d["filepath"] for d in self.dataset[:4]]

        run1 = self.pipeline.rank_resumes(paths, self.jd_path)
        run2 = self.pipeline.rank_resumes(paths, self.jd_path)
        run3 = self.pipeline.rank_resumes(paths, self.jd_path)

        order1 = [c["screening_report"]["candidate_name"] for c in run1["ranked_results"]]
        order2 = [c["screening_report"]["candidate_name"] for c in run2["ranked_results"]]
        order3 = [c["screening_report"]["candidate_name"] for c in run3["ranked_results"]]

        self.assertEqual(order1, order2)
        self.assertEqual(order2, order3)

    def test_3_safe_error_handling_for_invalid_jd(self):
        """Invalid or empty JD text input must raise explicit ValueError safely."""
        clean_path = self.dataset[0]["filepath"]

        with self.assertRaises(ValueError):
            self.pipeline.screen_resume(clean_path, jd_source="")


if __name__ == "__main__":
    unittest.main()
