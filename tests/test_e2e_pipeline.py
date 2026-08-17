"""
End-to-End Pipeline Test Suite for SECUROXI AI Scanner.
Validates 8 required end-to-end scenarios:
1. Clean resume -> SAFE
2. Legitimate small text -> NOT HIGH_RISK
3. White/hidden text only -> Visual finding
4. Clear prompt injection in visible text -> Prompt injection finding
5. Hidden prompt injection -> Correlated risk
6. Hidden ATS ranking manipulation -> HIGH_RISK
7. Malformed / corrupted PDF -> Graceful failure report
8. Empty document -> Graceful handling
"""

import sys
import os
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.models import Verdict, AttackCategory
from securoxi.scanner import SecuroxiScanner


class TestE2EPipeline(unittest.TestCase):

    def setUp(self):
        self.scanner = SecuroxiScanner()
        self.fixtures_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))

    def test_1_clean_resume_end_to_end(self):
        """Clean resume should scan end-to-end and produce Verdict.SAFE."""
        pdf_path = os.path.join(self.fixtures_dir, "clean_1_normal_resume.pdf")
        report = self.scanner.scan(pdf_path)
        self.assertEqual(report.verdict, Verdict.SAFE)
        self.assertEqual(report.risk_score, 0)
        self.assertEqual(len(report.findings), 0)

    def test_2_legitimate_small_text_not_high_risk(self):
        """Legitimate small text footnote should not produce HIGH_RISK."""
        pdf_path = os.path.join(self.fixtures_dir, "clean_2_small_footnote.pdf")
        report = self.scanner.scan(pdf_path)
        self.assertNotEqual(report.verdict, Verdict.HIGH_RISK)

    def test_3_white_hidden_text_visual_finding(self):
        """White font color text on white canvas should generate visual white text finding."""
        pdf_path = os.path.join(self.fixtures_dir, "visual_6_white_text.pdf")
        report = self.scanner.scan(pdf_path)
        categories = [f.category for f in report.findings]
        self.assertIn(AttackCategory.WHITE_TEXT, categories)

    def test_4_visible_prompt_injection(self):
        """Visible text prompt injection should produce prompt injection finding."""
        pdf_path = os.path.join(self.fixtures_dir, "injection_10_ignore_previous.pdf")
        report = self.scanner.scan(pdf_path)
        self.assertEqual(report.verdict, Verdict.SUSPICIOUS)
        categories = [f.category for f in report.findings]
        self.assertIn(AttackCategory.INSTRUCTION_OVERRIDE, categories)

    def test_5_hidden_prompt_injection_correlated_risk(self):
        """Hidden micro text + instruction override should produce correlated risk and HIGH_RISK."""
        pdf_path = os.path.join(self.fixtures_dir, "combined_16_hidden_plus_injection.pdf")
        report = self.scanner.scan(pdf_path)
        self.assertEqual(report.verdict, Verdict.HIGH_RISK)
        self.assertGreaterEqual(len(report.correlated_evidence), 1)

    def test_6_hidden_ats_ranking_manipulation(self):
        """White text + ATS 10/10 manipulation should produce HIGH_RISK verdict."""
        pdf_path = os.path.join(self.fixtures_dir, "combined_17_white_plus_ats.pdf")

        report = self.scanner.scan(pdf_path)
        self.assertEqual(report.verdict, Verdict.HIGH_RISK)
        self.assertEqual(report.risk_score, 100)

    def test_7_malformed_corrupted_pdf_graceful_failure(self):
        """Corrupted PDF scanning should fail gracefully without crashing."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"CORRUPTED_NON_PDF_BYTES")
            corrupted_path = f.name

        try:
            report = self.scanner.scan(corrupted_path)
            self.assertIsNotNone(report)
            self.assertEqual(report.verdict, Verdict.SUSPICIOUS)
            self.assertEqual(report.primary_threat, "DOCUMENT_PARSE_ERROR")
        finally:
            if os.path.exists(corrupted_path):
                os.remove(corrupted_path)

    def test_8_empty_document_graceful_handling(self):
        """Empty PDF file scanning should handle gracefully."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"")  # 0 byte file
            empty_path = f.name

        try:
            report = self.scanner.scan(empty_path)
            self.assertIsNotNone(report)
            self.assertEqual(report.verdict, Verdict.SUSPICIOUS)
        finally:
            if os.path.exists(empty_path):
                os.remove(empty_path)


if __name__ == "__main__":
    unittest.main()
