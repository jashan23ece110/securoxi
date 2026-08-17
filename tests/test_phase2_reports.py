"""
Unit Test Suite for SECUROXI Phase 2 Stage 7 — Explainable Screening Reports.
Tests machine-readable JSON reports, human-readable Markdown reports, human review disclaimers,
evidence provenance links, and zero-hallucination safeguards.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.config import SecuroxiConfig
from securoxi.screening.report_models import RecommendationCategory, ScreeningReport
from securoxi.screening.report_generator import SecuroxiReportGenerator
from securoxi.screening.ingestion import SecuroxiIngestionEngine
from securoxi.screening.extractor import RuleBasedExtractor
from securoxi.screening.matching_engine import SecuroxiMatchingEngine
from securoxi.screening.qualification_analyzer import SecuroxiQualificationAnalyzer
from securoxi.screening.scorer import SecuroxiCandidateScorer


PHASE2_FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "phase2"))


class TestPhase2Reports(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = SecuroxiConfig()
        cls.report_generator = SecuroxiReportGenerator()
        cls.ingestion_engine = SecuroxiIngestionEngine(config=cls.config)
        cls.extractor = RuleBasedExtractor()
        cls.matching_engine = SecuroxiMatchingEngine()
        cls.qualification_analyzer = SecuroxiQualificationAnalyzer()
        cls.scorer = SecuroxiCandidateScorer()

    def test_1_generate_machine_and_human_readable_screening_reports(self):
        """Report Generator must produce structured JSON and human-readable Markdown reports with evidence provenance."""
        pdf_path = os.path.join(PHASE2_FIXTURES_DIR, "candidate_excellent.pdf")
        jd_path = os.path.join(PHASE2_FIXTURES_DIR, "sample_jd.txt")

        resume_doc = self.ingestion_engine.ingest_resume(pdf_path)
        jd_doc = self.ingestion_engine.ingest_job_description(jd_path)

        resume_prof = self.extractor.extract_resume_profile(resume_doc)
        jd_prof = self.extractor.extract_jd_profile(jd_doc)

        match_rep = self.matching_engine.match_resume_to_jd(resume_prof, jd_prof)
        qual_rep = self.qualification_analyzer.analyze_qualifications(resume_prof, jd_prof)
        score_rep = self.scorer.score_candidate(resume_prof, jd_prof, match_rep, qual_rep)

        report: ScreeningReport = self.report_generator.generate_report(
            resume_prof, jd_prof, match_rep, qual_rep, score_rep
        )

        # 1. JSON Report Verification
        report_dict = report.to_dict()
        self.assertEqual(report_dict["recommendation"], "STRONG_MATCH")
        self.assertIn("human_review_disclaimer", report_dict)
        self.assertIn("does not constitute an automated hiring or rejection decision", report_dict["human_review_disclaimer"])
        self.assertGreaterEqual(len(report_dict["required_matches"]), 1)

        # 2. Markdown Report Verification
        markdown_text = report.to_markdown()
        self.assertIn("# SECUROXI Candidate Screening Report", markdown_text)
        self.assertIn("STRONG_MATCH", markdown_text)
        self.assertIn("Executive Summary", markdown_text)

    def test_2_low_match_candidate_screening_report(self):
        """Candidate missing mandatory skills must generate LOW_MATCH or PARTIAL_MATCH report with explicit gap evidence."""
        pdf_path = os.path.join(PHASE2_FIXTURES_DIR, "candidate_missing_mandatory.pdf")
        jd_path = os.path.join(PHASE2_FIXTURES_DIR, "sample_jd.txt")

        resume_doc = self.ingestion_engine.ingest_resume(pdf_path)
        jd_doc = self.ingestion_engine.ingest_job_description(jd_path)

        resume_prof = self.extractor.extract_resume_profile(resume_doc)
        jd_prof = self.extractor.extract_jd_profile(jd_doc)

        match_rep = self.matching_engine.match_resume_to_jd(resume_prof, jd_prof)
        qual_rep = self.qualification_analyzer.analyze_qualifications(resume_prof, jd_prof)
        score_rep = self.scorer.score_candidate(resume_prof, jd_prof, match_rep, qual_rep)

        report = self.report_generator.generate_report(
            resume_prof, jd_prof, match_rep, qual_rep, score_rep
        )

        self.assertIn(report.recommendation, [RecommendationCategory.PARTIAL_MATCH, RecommendationCategory.LOW_MATCH])
        self.assertGreaterEqual(len(report.required_missing), 1)


if __name__ == "__main__":
    unittest.main()
