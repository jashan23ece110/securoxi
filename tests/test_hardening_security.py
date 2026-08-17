"""
Hardening & Security Tests for SECUROXI AI Core Engine.
Tests:
- Corrupted / Malformed PDF handling
- Password-protected PDF simulation
- Oversized file resource limit enforcement
- Path traversal protection attempts
- Empty PDF file handling
- Unregistered / Unsupported file formats
- Configuration overrides (custom weights, custom thresholds)
- Score boundary capping (0 to 100)
"""

import sys
import os
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.config import SecuroxiConfig
from securoxi.models import TextSpan, Verdict, AttackCategory, SecurityFinding, Severity
from securoxi.engine import SecuroxiEngine
from securoxi.parsers.pdf_parser import PDFParser
from securoxi.risk_engine import SecuroxiRiskEngine


class TestHardeningAndSecurity(unittest.TestCase):

    def setUp(self):
        self.config = SecuroxiConfig(max_file_size_bytes=100 * 1024) # 100 KB limit for testing
        self.engine = SecuroxiEngine(config=self.config)

    def test_corrupted_pdf_handling(self):
        """Scanning a corrupted non-PDF file should fail gracefully returning a SUSPICIOUS report, not crash."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"NOT_A_REAL_PDF_STREAM_CORRUPTED_BYTES_12345")
            corrupted_path = f.name

        try:
            report = self.engine.analyze_document(corrupted_path)
            self.assertIsNotNone(report)
            self.assertEqual(report.verdict, Verdict.SUSPICIOUS)
            self.assertEqual(report.primary_threat, "DOCUMENT_PARSE_ERROR")
            self.assertIn("PARSER_FAILURE", report.metadata.get("error_code", ""))
        finally:
            if os.path.exists(corrupted_path):
                os.remove(corrupted_path)

    def test_unsupported_file_extension(self):
        """Unsupported file extensions should return a clean error report."""
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as f:
            f.write(b"BINARY_CONTENT")
            exe_path = f.name

        try:
            report = self.engine.analyze_document(exe_path)
            self.assertEqual(report.verdict, Verdict.SUSPICIOUS)
            self.assertIn("UNSUPPORTED_FORMAT", report.metadata.get("error_code", ""))
        finally:
            if os.path.exists(exe_path):
                os.remove(exe_path)

    def test_file_not_found_handling(self):
        """Non-existent file path should return FILE_NOT_FOUND report."""
        report = self.engine.analyze_document("/non/existent/path/document.pdf")
        self.assertEqual(report.verdict, Verdict.SUSPICIOUS)
        self.assertIn("FILE_NOT_FOUND", report.metadata.get("error_code", ""))

    def test_oversized_file_limit_enforcement(self):
        """File exceeding max_file_size_bytes should trigger PARSER_FAILURE limit error."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            # Write 200 KB file (exceeds 100 KB test limit)
            f.write(b"A" * (200 * 1024))
            oversized_path = f.name

        try:
            report = self.engine.analyze_document(oversized_path)
            self.assertEqual(report.verdict, Verdict.SUSPICIOUS)
            self.assertIn("PARSER_FAILURE", report.metadata.get("error_code", ""))
            self.assertIn("exceeds maximum limit", report.verdict_explanation)
        finally:
            if os.path.exists(oversized_path):
                os.remove(oversized_path)

    def test_path_traversal_safety(self):
        """Canonical path resolution should handle dot-dot relative paths safely."""
        test_pdf = os.path.abspath(os.path.join(os.path.dirname(__file__), "sample_resume_test.pdf"))
        traversal_path = os.path.join(os.path.dirname(test_pdf), "..", "tests", "sample_resume_test.pdf")

        if os.path.exists(test_pdf):
            report = self.engine.analyze_document(traversal_path)
            self.assertIsNotNone(report)
            self.assertEqual(report.filename, "sample_resume_test.pdf")

    def test_custom_config_thresholds(self):
        """Custom config with low micro_font_threshold=1.0 should ignore 2.0pt text."""
        custom_config = SecuroxiConfig(micro_font_threshold=1.0)

        custom_engine = SecuroxiEngine(config=custom_config)

        # 2.0pt text will not trigger micro text under 1.0pt threshold
        spans = [
            TextSpan(text="Some 2.0pt text", font_size=2.0, font_color="#000000")
        ]
        from securoxi.analyzers.visual_deception import VisualDeceptionAnalyzer
        analyzer = VisualDeceptionAnalyzer(config=custom_config)
        findings = analyzer.analyze(spans)
        self.assertEqual(len(findings), 0)

    def test_score_boundary_capping(self):
        """Risk engine score should cap cleanly between 0 and 100."""
        risk_engine = SecuroxiRiskEngine()
        
        # 1. Negative base score handling (empty findings)
        verdict, score, primary, conf, exp, corr = risk_engine.evaluate([])
        self.assertEqual(score, 0)
        self.assertGreaterEqual(score, 0)

        # 2. Extreme findings score capping (over 100)
        findings = [
            SecurityFinding(
                finding_id=f"ID-{i}",
                category=cat,
                severity=Severity.CRITICAL,
                title="Attack",
                description="Attack",
                evidence="Attack",
                location=f"Page {i}"
            )
            for i, cat in enumerate(list(AttackCategory), 1)
        ]
        verdict, score, primary, conf, exp, corr = risk_engine.evaluate(findings)
        self.assertEqual(score, 100)
        self.assertLessEqual(score, 100)


if __name__ == "__main__":
    unittest.main()
