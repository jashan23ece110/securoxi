"""
Unit Test Suite for SECUROXI Phase 2 Stage 4 — Semantic Matching Engine.
Tests exact skill match, normalized match, semantic related match, distinct technology handling
(React vs React Native), missing skills, and experience evaluation.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.config import SecuroxiConfig
from securoxi.screening.models import ResumeDocument, JobDescriptionDocument
from securoxi.screening.ingestion import SecuroxiIngestionEngine
from securoxi.screening.extractor import RuleBasedExtractor
from securoxi.screening.matching_engine import SecuroxiMatchingEngine
from securoxi.screening.matching_models import MatchStatus, MatchType, MatchingReport


PHASE2_FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "phase2"))


class TestPhase2Matching(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = SecuroxiConfig()
        cls.ingestion_engine = SecuroxiIngestionEngine(config=cls.config)
        cls.extractor = RuleBasedExtractor()
        cls.matching_engine = SecuroxiMatchingEngine()

    def test_1_exact_and_normalized_matches(self):
        """Exact skill names and normalized aliases must result in MATCH status."""
        pdf_path = os.path.join(PHASE2_FIXTURES_DIR, "sarah_resume.pdf")
        jd_path = os.path.join(PHASE2_FIXTURES_DIR, "sample_jd.txt")

        resume_doc = self.ingestion_engine.ingest_resume(pdf_path)
        jd_doc = self.ingestion_engine.ingest_job_description(jd_path)

        resume_prof = self.extractor.extract_resume_profile(resume_doc)
        jd_prof = self.extractor.extract_jd_profile(jd_doc)

        report: MatchingReport = self.matching_engine.match_resume_to_jd(resume_prof, jd_prof)

        self.assertEqual(report.resume_id, resume_prof.resume_id)
        self.assertEqual(report.jd_id, jd_prof.jd_id)
        self.assertGreaterEqual(report.matched_required_count, 1)

        # Check Python match
        python_match = next((m for m in report.required_skill_matches if "Python" in m.requirement), None)
        self.assertIsNotNone(python_match)
        self.assertEqual(python_match.match_status, MatchStatus.MATCH)

    def test_2_semantic_related_technology_match(self):
        """Related technology in same domain (e.g. PostgreSQL vs MySQL) must result in PARTIAL_MATCH."""
        pdf_path = os.path.join(PHASE2_FIXTURES_DIR, "sarah_resume.pdf") # Has PostgreSQL
        resume_doc = self.ingestion_engine.ingest_resume(pdf_path)
        resume_prof = self.extractor.extract_resume_profile(resume_doc)

        # Create mock JD requiring MySQL
        jd_doc = self.ingestion_engine.ingest_job_description("DATABASE ROLE\nREQUIREMENTS\n- 5+ years experience in MySQL")
        jd_prof = self.extractor.extract_jd_profile(jd_doc)

        report = self.matching_engine.match_resume_to_jd(resume_prof, jd_prof)
        mysql_match = next((m for m in report.required_skill_matches if "Mysql" in m.requirement or "MySQL" in m.requirement), None)

        self.assertIsNotNone(mysql_match)
        self.assertEqual(mysql_match.match_status, MatchStatus.PARTIAL_MATCH)
        self.assertEqual(mysql_match.match_type, MatchType.SEMANTIC_RELATED)

    def test_3_distinctness_guard_react_vs_react_native(self):
        """React and React Native must NOT automatically become full MATCH."""
        pdf_path = os.path.join(PHASE2_FIXTURES_DIR, "sarah_resume.pdf")
        resume_doc = self.ingestion_engine.ingest_resume(pdf_path)
        resume_prof = self.extractor.extract_resume_profile(resume_doc)

        # Create JD requiring React Native
        jd_doc = self.ingestion_engine.ingest_job_description("MOBILE ROLE\nREQUIREMENTS\n- 3+ years experience in React Native")
        jd_prof = self.extractor.extract_jd_profile(jd_doc)

        report = self.matching_engine.match_resume_to_jd(resume_prof, jd_prof)
        rn_match = report.required_skill_matches[0]

        self.assertNotEqual(rn_match.match_status, MatchStatus.MATCH)
        self.assertEqual(rn_match.match_status, MatchStatus.NO_MATCH)

    def test_4_missing_required_skill_returns_no_match(self):
        """Missing required skills must return NO_MATCH."""
        pdf_path = os.path.join(PHASE2_FIXTURES_DIR, "sarah_resume.pdf")
        resume_doc = self.ingestion_engine.ingest_resume(pdf_path)
        resume_prof = self.extractor.extract_resume_profile(resume_doc)

        jd_doc = self.ingestion_engine.ingest_job_description("RUST ROLE\nREQUIREMENTS\n- 5+ years experience in Rust")
        jd_prof = self.extractor.extract_jd_profile(jd_doc)

        report = self.matching_engine.match_resume_to_jd(resume_prof, jd_prof)
        rust_match = report.required_skill_matches[0]

        self.assertEqual(rust_match.match_status, MatchStatus.NO_MATCH)
        self.assertEqual(rust_match.match_type, MatchType.NO_MATCH)

    def test_5_experience_requirement_evaluation(self):
        """Candidate experience meeting or exceeding JD requirement must result in EXPERIENCE_MATCH."""
        pdf_path = os.path.join(PHASE2_FIXTURES_DIR, "sarah_resume.pdf") # 6.0 yrs
        resume_doc = self.ingestion_engine.ingest_resume(pdf_path)
        resume_prof = self.extractor.extract_resume_profile(resume_doc)

        jd_doc = self.ingestion_engine.ingest_job_description("SENIOR ROLE\nREQUIREMENTS\n- 5+ years experience")
        jd_prof = self.extractor.extract_jd_profile(jd_doc)

        report = self.matching_engine.match_resume_to_jd(resume_prof, jd_prof)
        self.assertIsNotNone(report.experience_match)
        self.assertEqual(report.experience_match.match_status, MatchStatus.MATCH)
        self.assertEqual(report.experience_match.match_type, MatchType.EXPERIENCE_MATCH)


if __name__ == "__main__":
    unittest.main()
