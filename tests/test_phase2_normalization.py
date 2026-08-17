"""
Unit Test Suite for SECUROXI Phase 2 Stage 3 — Skill & Requirement Normalization.
Tests alias resolution, distinctness rules (C vs C++ vs C#, Java vs JavaScript),
experience numerical bounds, education normalization, and original wording preservation.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.screening.normalizer import SecuroxiNormalizer
from securoxi.screening.normalization_models import (
    NormalizedSkill,
    NormalizedExperienceRequirement,
    NormalizedEducationRequirement
)


class TestPhase2Normalization(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.normalizer = SecuroxiNormalizer()

    def test_1_alias_resolution(self):
        """Skill aliases must resolve to canonical representations while preserving original raw text."""
        test_cases = [
            ("JS", "JavaScript", "Language"),
            ("javascript", "JavaScript", "Language"),
            ("Node", "Node.js", "Framework"),
            ("nodejs", "Node.js", "Framework"),
            ("Postgres", "PostgreSQL", "Database"),
            ("postgresql", "PostgreSQL", "Database"),
            ("K8s", "Kubernetes", "Tool"),
            ("kubernetes", "Kubernetes", "Tool"),
            ("Golang", "Go", "Language"),
            ("Python developer", "Python", "Language"),
            ("AWS Lambda", "AWS Lambda", "Cloud"),
        ]

        for raw_text, expected_canonical, expected_category in test_cases:
            norm: NormalizedSkill = self.normalizer.normalize_skill(raw_text)
            self.assertEqual(norm.canonical_name, expected_canonical, f"Failed resolving '{raw_text}'")
            self.assertEqual(norm.raw_text, raw_text)
            self.assertEqual(norm.category, expected_category)

    def test_2_distinctness_rules(self):
        """C, C++, C#, Java, and JavaScript must remain strictly distinct."""
        norm_c = self.normalizer.normalize_skill("C")

        norm_cpp = self.normalizer.normalize_skill("C++")
        norm_csharp = self.normalizer.normalize_skill("C#")
        norm_java = self.normalizer.normalize_skill("Java")
        norm_js = self.normalizer.normalize_skill("JavaScript")

        self.assertEqual(norm_c.canonical_name, "C")
        self.assertEqual(norm_cpp.canonical_name, "C++")
        self.assertEqual(norm_csharp.canonical_name, "C#")
        self.assertEqual(norm_java.canonical_name, "Java")
        self.assertEqual(norm_js.canonical_name, "JavaScript")

        self.assertNotEqual(norm_c.canonical_name, norm_cpp.canonical_name)
        self.assertNotEqual(norm_cpp.canonical_name, norm_csharp.canonical_name)
        self.assertNotEqual(norm_java.canonical_name, norm_js.canonical_name)

    def test_3_experience_normalization(self):
        """Experience expressions must parse numerical min and max years bounds."""
        exp1 = self.normalizer.normalize_experience("5+ years of experience in Python")
        self.assertEqual(exp1.min_years, 5.0)
        self.assertIsNone(exp1.max_years)

        exp2 = self.normalizer.normalize_experience("3-5 yrs in software engineering")
        self.assertEqual(exp2.min_years, 3.0)
        self.assertEqual(exp2.max_years, 5.0)

    def test_4_education_normalization(self):
        """Education text must normalize degree level and field of study."""
        edu1 = self.normalizer.normalize_education("BS in Computer Science")
        self.assertEqual(edu1.degree_level, "Bachelor's Degree")

        edu2 = self.normalizer.normalize_education("MS Degree in Software Engineering")
        self.assertEqual(edu2.degree_level, "Master's Degree")

    def test_5_normalize_skills_list_deduplication(self):
        """normalizing a list with aliases (['JS', 'JavaScript', 'Python']) must deduplicate to canonical names."""
        raw_list = ["JS", "JavaScript", "Python", "python3", "Docker", "k8s"]
        normalized_list = self.normalizer.normalize_skills_list(raw_list)
        canonical_names = [s.canonical_name for s in normalized_list]

        self.assertEqual(len(canonical_names), 4)
        self.assertEqual(canonical_names, ["JavaScript", "Python", "Docker", "Kubernetes"])


if __name__ == "__main__":
    unittest.main()
