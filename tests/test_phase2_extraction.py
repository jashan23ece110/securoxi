"""
Unit Test Suite for SECUROXI Phase 2 Stage 2 — Structured Information Extraction.
Tests candidate name, skills taxonomy, work experience, education, JD requirements,
provenance tracking, and graceful UNKNOWN fallback handling.
"""

import sys
import os
import unittest
import pymupdf as fitz

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.config import SecuroxiConfig
from securoxi.screening.ingestion import SecuroxiIngestionEngine
from securoxi.screening.extractor import RuleBasedExtractor
from securoxi.screening.extraction_models import ExtractedResumeProfile, ExtractedJDProfile


PHASE2_FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "phase2"))


def setup_extraction_fixtures():
    """Helper to generate detailed extraction test PDF fixtures."""
    os.makedirs(PHASE2_FIXTURES_DIR, exist_ok=True)

    # 1. Full Technical Resume PDF
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text(fitz.Point(50, 40), "SARAH CONNOR", fontsize=16)
    page.insert_text(fitz.Point(50, 70), "SUMMARY\nSenior Cloud Security Engineer specializing in Kubernetes and Python.", fontsize=10)
    page.insert_text(fitz.Point(50, 130), "SKILLS\nLanguages: Python, Go, SQL. Tools: Docker, Kubernetes, AWS, PostgreSQL.", fontsize=10)
    page.insert_text(fitz.Point(50, 200), "EXPERIENCE\nSenior Infrastructure Engineer at Cyberdyne (2020 - 2026)\nBuilt zero-trust microservices.", fontsize=10)
    page.insert_text(fitz.Point(50, 280), "EDUCATION\nB.S. in Computer Science, Stanford University (2019)", fontsize=10)
    page.insert_text(fitz.Point(50, 340), "PROJECTS\nSecuroxi Engine: Built PDF prompt injection defense framework.", fontsize=10)
    doc.save(os.path.join(PHASE2_FIXTURES_DIR, "sarah_resume.pdf"))
    doc.close()

    # 2. Minimal Resume with Missing Sections
    doc_min = fitz.open()
    page_min = doc_min.new_page(width=595, height=842)
    page_min.insert_text(fitz.Point(50, 50), "MINIMAL CANDIDATE\nJust basic HTML skills.", fontsize=11)
    doc_min.save(os.path.join(PHASE2_FIXTURES_DIR, "minimal_resume.pdf"))
    doc_min.close()


class TestPhase2Extraction(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        setup_extraction_fixtures()
        cls.config = SecuroxiConfig()
        cls.ingestion_engine = SecuroxiIngestionEngine(config=cls.config)
        cls.extractor = RuleBasedExtractor()

    def test_1_extract_structured_resume_profile(self):
        """RuleBasedExtractor must extract candidate name, summary, skill taxonomy, experience, and education."""
        pdf_path = os.path.join(PHASE2_FIXTURES_DIR, "sarah_resume.pdf")
        resume = self.ingestion_engine.ingest_resume(pdf_path)
        profile: ExtractedResumeProfile = self.extractor.extract_resume_profile(resume)

        self.assertEqual(profile.candidate_name, "SARAH CONNOR")
        self.assertIn("Python", profile.skills.programming_languages)
        self.assertIn("Go", profile.skills.programming_languages)
        self.assertIn("Docker", profile.skills.tools)
        self.assertIn("AWS", profile.skills.cloud_platforms)
        self.assertGreaterEqual(profile.total_years_experience, 5.0)
        self.assertGreaterEqual(len(profile.education), 1)
        self.assertEqual(profile.education[0].degree, "Bachelor of Science")
        self.assertIn("candidate_name", profile.field_provenance)

    def test_2_extract_minimal_resume_handles_unknowns_gracefully(self):
        """Resume missing summary, education, or experience sections must return UNKNOWN / NOT_SPECIFIED gracefully."""
        pdf_path = os.path.join(PHASE2_FIXTURES_DIR, "minimal_resume.pdf")
        resume = self.ingestion_engine.ingest_resume(pdf_path)
        profile: ExtractedResumeProfile = self.extractor.extract_resume_profile(resume)

        self.assertEqual(profile.summary, "NOT_SPECIFIED")
        self.assertEqual(len(profile.education), 0)
        self.assertEqual(profile.total_years_experience, 0.0)
        self.assertGreaterEqual(profile.extraction_confidence, 0.80)

    def test_3_extract_structured_jd_profile(self):
        """RuleBasedExtractor must extract job title, required skills, min experience, and responsibilities from JD."""
        jd_path = os.path.join(PHASE2_FIXTURES_DIR, "sample_jd.txt")
        jd = self.ingestion_engine.ingest_job_description(jd_path)
        jd_profile: ExtractedJDProfile = self.extractor.extract_jd_profile(jd)

        self.assertEqual(jd_profile.job_title, "SENIOR PYTHON SECURITY ENGINEER")
        self.assertIn("Python", jd_profile.required_skills)
        self.assertGreaterEqual(jd_profile.minimum_experience_years, 5.0)
        self.assertGreaterEqual(len(jd_profile.responsibilities), 1)
        self.assertIn("minimum_experience_years", jd_profile.field_provenance)


if __name__ == "__main__":
    unittest.main()
