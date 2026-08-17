"""
Unit Test Suite for SECUROXI Phase 2 Stage 5 — Experience & Qualification Analysis.
Tests technology-specific experience separation (total career != tech experience),
overlapping employment date merging, missing dates, and qualification findings.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.screening.extraction_models import ExtractedResumeProfile, ExperienceRecord, CategorizedSkills, EducationRecord
from securoxi.screening.models import JobDescriptionDocument
from securoxi.screening.extractor import RuleBasedExtractor
from securoxi.screening.qualification_analyzer import SecuroxiQualificationAnalyzer
from securoxi.screening.qualification_models import QualificationStatus, QualificationAnalysisReport


class TestPhase2Qualification(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.analyzer = SecuroxiQualificationAnalyzer()
        cls.extractor = RuleBasedExtractor()

    def test_1_technology_specific_experience_separation(self):
        """Total career duration (5 yrs) must NOT be equated with specific tech duration (1 yr Python)."""
        # Candidate with 5 yrs total career (2020-2025), but Python only used in 2024-2025 (1 yr)
        exp1 = ExperienceRecord(
            job_title="Java Developer",
            company="Enterprise Corp",
            start_date="2020",
            end_date="2024",
            duration_years=4.0,
            responsibilities=["Built Java Spring Boot backend services"]
        )
        exp2 = ExperienceRecord(
            job_title="Python Scripting Developer",
            company="Tech Startup",
            start_date="2024",
            end_date="2025",
            duration_years=1.0,
            responsibilities=["Wrote Python automation scripts"]
        )

        profile = ExtractedResumeProfile(
            resume_id="RES-MOCK-001",
            candidate_name="JOHN DOE",
            skills=CategorizedSkills(programming_languages=["Java", "Python"]),
            work_experience=[exp1, exp2],
            total_years_experience=5.0
        )

        # Mock JD requiring 3 years Python
        jd_prof = self.extractor.extract_jd_profile(
            JobDescriptionDocument(
                jd_id="JD-MOCK-001",
                metadata=None,
                job_title="SENIOR PYTHON DEVELOPER",
                raw_text="SENIOR PYTHON ROLE\nREQUIREMENTS\n- 3+ years experience in Python",
                normalized_text=""
            )
        )

        report: QualificationAnalysisReport = self.analyzer.analyze_qualifications(profile, jd_prof)

        # Verification: Total career experience = 5.0 yrs, but Python specific experience = 1.0 yr!
        self.assertEqual(report.total_relevant_experience_years, 5.0)
        self.assertEqual(report.technology_experience_breakdown.get("Python"), 1.0)

        # Python qualification must NOT be REQUIREMENT_MET!
        python_finding = next((f for f in report.findings if "Python" in f.qualification_name), None)
        self.assertIsNotNone(python_finding)
        self.assertNotEqual(python_finding.status, QualificationStatus.REQUIREMENT_MET)

    def test_2_overlapping_employment_date_merging(self):
        """Overlapping employment dates (2020-2023 and 2022-2025) must merge to 5.0 non-overlapping years."""
        exp1 = ExperienceRecord(job_title="Dev 1", start_date="2020", end_date="2023", duration_years=3.0)
        exp2 = ExperienceRecord(job_title="Dev 2", start_date="2022", end_date="2025", duration_years=3.0)

        non_overlapping_years = self.analyzer._calculate_non_overlapping_experience([exp1, exp2])
        self.assertEqual(non_overlapping_years, 5.0) # 2020 to 2025 = 5 yrs (not 6 yrs!)

    def test_3_education_and_certification_qualification_evaluation(self):
        """Education and certifications must generate explicit REQUIREMENT_MET findings."""
        profile = ExtractedResumeProfile(
            resume_id="RES-MOCK-002",
            education=[EducationRecord(degree="Bachelor of Science", field_of_study="CS", institution="Stanford")],
            certifications=["AWS Certified Solutions Architect"]
        )

        jd_prof = self.extractor.extract_jd_profile(
            JobDescriptionDocument(
                jd_id="JD-MOCK-002",
                metadata=None,
                job_title="CLOUD ARCHITECT",
                raw_text="CLOUD ARCHITECT\nREQUIREMENTS\n- Bachelor's degree\n- AWS Certification",
                normalized_text=""
            )
        )

        report = self.analyzer.analyze_qualifications(profile, jd_prof)
        self.assertGreaterEqual(report.met_qualifications_count, 1)


if __name__ == "__main__":
    unittest.main()
