"""
Unit Test Suite for SECUROXI Phase 2 Stage 6 — Candidate Scoring & Ranking.
Tests candidate fit score calculation, mandatory missing skill penalty ceiling,
multi-candidate ranking order, and ranking sensitivity tests.
"""

import sys
import os
import unittest
import pymupdf as fitz

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.config import SecuroxiConfig
from securoxi.screening.scoring_models import ScoringWeights, CandidateScoreReport, RankedCandidatesReport
from securoxi.screening.scorer import SecuroxiCandidateScorer, SecuroxiRankingEngine
from securoxi.screening.extraction_models import ExtractedResumeProfile, CategorizedSkills, ExperienceRecord, EducationRecord
from securoxi.screening.models import JobDescriptionDocument
from securoxi.screening.ingestion import SecuroxiIngestionEngine
from securoxi.screening.extractor import RuleBasedExtractor
from securoxi.screening.matching_engine import SecuroxiMatchingEngine
from securoxi.screening.qualification_analyzer import SecuroxiQualificationAnalyzer


PHASE2_FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "phase2"))


def setup_scoring_fixtures():
    """Helper to generate multi-candidate resume fixtures."""
    os.makedirs(PHASE2_FIXTURES_DIR, exist_ok=True)

    # 1. Candidate 1: Excellent Match (Sarah Connor) - python, pymupdf, fastapi, cybersecurity, llm security, 6 yrs
    doc1 = fitz.open()
    p1 = doc1.new_page(width=595, height=842)
    p1.insert_text(fitz.Point(50, 40), "SARAH CONNOR", fontsize=16)
    p1.insert_text(fitz.Point(50, 80), "SUMMARY\nSenior Python Security Engineer specializing in LLM Security.", fontsize=10)
    p1.insert_text(fitz.Point(50, 140), "SKILLS\nPython, PyMuPDF, FastAPI, Cybersecurity, LLM Security, Prompt Injection Defense, Go, Docker, AWS, PostgreSQL.", fontsize=10)
    p1.insert_text(fitz.Point(50, 200), "EXPERIENCE\nSenior Security Engineer (2020 - 2026)\nBuilt PDF prompt injection defense framework.", fontsize=10)
    p1.insert_text(fitz.Point(50, 260), "EDUCATION\nB.S. in Computer Science (2019)", fontsize=10)
    doc1.save(os.path.join(PHASE2_FIXTURES_DIR, "candidate_excellent.pdf"))
    doc1.close()


    # 2. Candidate 2: Missing Mandatory Skill (John Doe) - Has 10 yrs Java, but NO Python!
    doc2 = fitz.open()
    p2 = doc2.new_page(width=595, height=842)
    p2.insert_text(fitz.Point(50, 40), "JOHN DOE", fontsize=16)
    p2.insert_text(fitz.Point(50, 80), "SUMMARY\nJava Enterprise Architect.", fontsize=10)
    p2.insert_text(fitz.Point(50, 140), "SKILLS\nJava, Spring Boot, MySQL, Oracle.", fontsize=10)
    p2.insert_text(fitz.Point(50, 200), "EXPERIENCE\nLead Architect (2015 - 2025)\nBuilt banking systems.", fontsize=10)
    doc2.save(os.path.join(PHASE2_FIXTURES_DIR, "candidate_missing_mandatory.pdf"))
    doc2.close()


class TestPhase2Scoring(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        setup_scoring_fixtures()
        cls.config = SecuroxiConfig()
        cls.scorer = SecuroxiCandidateScorer()
        cls.ranking_engine = SecuroxiRankingEngine()
        cls.ingestion_engine = SecuroxiIngestionEngine(config=cls.config)
        cls.extractor = RuleBasedExtractor()
        cls.matching_engine = SecuroxiMatchingEngine()
        cls.qualification_analyzer = SecuroxiQualificationAnalyzer()

    def test_1_excellent_candidate_fit_score(self):
        """Candidate satisfying all required skills and experience must receive fit score >= 85.0 (EXCELLENT_FIT)."""
        pdf_path = os.path.join(PHASE2_FIXTURES_DIR, "candidate_excellent.pdf")
        jd_path = os.path.join(PHASE2_FIXTURES_DIR, "sample_jd.txt")

        resume_doc = self.ingestion_engine.ingest_resume(pdf_path)
        jd_doc = self.ingestion_engine.ingest_job_description(jd_path)

        resume_prof = self.extractor.extract_resume_profile(resume_doc)
        jd_prof = self.extractor.extract_jd_profile(jd_doc)

        match_rep = self.matching_engine.match_resume_to_jd(resume_prof, jd_prof)
        qual_rep = self.qualification_analyzer.analyze_qualifications(resume_prof, jd_prof)

        score_rep: CandidateScoreReport = self.scorer.score_candidate(resume_prof, jd_prof, match_rep, qual_rep)

        self.assertGreaterEqual(score_rep.fit_score, 85.0)
        self.assertEqual(score_rep.fit_category, "EXCELLENT_FIT")
        self.assertGreaterEqual(len(score_rep.strengths), 1)

    def test_2_missing_mandatory_skill_penalty_ceiling(self):
        """Candidate missing mandatory Python skill must be capped at fit_score <= 50.0 despite 10 yrs experience."""
        pdf_path = os.path.join(PHASE2_FIXTURES_DIR, "candidate_missing_mandatory.pdf")
        jd_path = os.path.join(PHASE2_FIXTURES_DIR, "sample_jd.txt") # Requires Python

        resume_doc = self.ingestion_engine.ingest_resume(pdf_path)
        jd_doc = self.ingestion_engine.ingest_job_description(jd_path)

        resume_prof = self.extractor.extract_resume_profile(resume_doc)
        jd_prof = self.extractor.extract_jd_profile(jd_doc)

        match_rep = self.matching_engine.match_resume_to_jd(resume_prof, jd_prof)
        qual_rep = self.qualification_analyzer.analyze_qualifications(resume_prof, jd_prof)

        score_rep: CandidateScoreReport = self.scorer.score_candidate(resume_prof, jd_prof, match_rep, qual_rep)

        # Verification: Missing mandatory Python skill caps fit score <= 50.0!
        self.assertLessEqual(score_rep.fit_score, 50.0)
        self.assertIn("gaps", score_rep.to_dict())
        self.assertGreaterEqual(len(score_rep.gaps), 1)

    def test_3_multi_candidate_ranking_order(self):
        """SecuroxiRankingEngine must rank candidates in descending order of fit score."""
        resumes = [
            os.path.join(PHASE2_FIXTURES_DIR, "candidate_missing_mandatory.pdf"),
            os.path.join(PHASE2_FIXTURES_DIR, "candidate_excellent.pdf")
        ]
        jd_path = os.path.join(PHASE2_FIXTURES_DIR, "sample_jd.txt")

        ranked_report: RankedCandidatesReport = self.ranking_engine.rank_candidates(resumes, jd_path)

        self.assertEqual(ranked_report.total_candidates, 2)
        # Sarah Connor (Excellent) must be ranked #1!
        self.assertEqual(ranked_report.ranked_candidates[0].candidate_name, "SARAH CONNOR")
        self.assertGreater(
            ranked_report.ranked_candidates[0].fit_score,
            ranked_report.ranked_candidates[1].fit_score
        )

    def test_4_ranking_sensitivity_with_custom_weights(self):
        """Custom weights must adjust candidate fit score calculation transparently."""
        custom_weights = ScoringWeights(
            required_skills_weight=0.70,
            experience_weight=0.10,
            preferred_skills_weight=0.10,
            education_cert_weight=0.10
        )
        custom_scorer = SecuroxiCandidateScorer(weights=custom_weights)

        pdf_path = os.path.join(PHASE2_FIXTURES_DIR, "candidate_excellent.pdf")
        jd_path = os.path.join(PHASE2_FIXTURES_DIR, "sample_jd.txt")

        resume_doc = self.ingestion_engine.ingest_resume(pdf_path)
        jd_doc = self.ingestion_engine.ingest_job_description(jd_path)

        resume_prof = self.extractor.extract_resume_profile(resume_doc)
        jd_prof = self.extractor.extract_jd_profile(jd_doc)

        match_rep = self.matching_engine.match_resume_to_jd(resume_prof, jd_prof)
        qual_rep = self.qualification_analyzer.analyze_qualifications(resume_prof, jd_prof)

        score_rep = custom_scorer.score_candidate(resume_prof, jd_prof, match_rep, qual_rep)
        self.assertGreaterEqual(score_rep.fit_score, 85.0)


if __name__ == "__main__":
    unittest.main()
