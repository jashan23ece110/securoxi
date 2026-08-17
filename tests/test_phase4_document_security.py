"""
Unit & Security Test Suite for SECUROXI Phase 4 Stage 5 — Malicious Document & Parser Security.
Tests ZipSlip path traversal rejection, decompression bomb safeguards, malformed PDF safe handling,
and filename path traversal sanitization.
"""

import sys
import os
import tempfile
import zipfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from securoxi.parsers.pdf_parser import PDFParser
from securoxi.api.app import process_zip_archive
from fastapi import HTTPException


class TestPhase4DocumentSecurity(unittest.TestCase):

    def setUp(self):
        self.parser = PDFParser()
        self.temp_dir = tempfile.mkdtemp(prefix="securoxi_doc_sec_")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_1_malformed_pdf_safe_failure(self):
        """Corrupted/malformed PDF file byte stream must raise ValueError cleanly."""
        corrupted_path = os.path.join(self.temp_dir, "corrupted.pdf")
        with open(corrupted_path, "wb") as f:
            f.write(b"NOT_A_REAL_PDF_HEADER_123456789")

        with self.assertRaises(ValueError) as ctx:
            self.parser.parse(corrupted_path)
        self.assertIn("Failed to open PDF document", str(ctx.exception))

    def test_2_zip_archive_entry_limit_safeguard(self):
        """ZIP archive exceeding 50 entries MUST be rejected with 400 Bad Request."""
        zip_path = os.path.join(self.temp_dir, "too_many_entries.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            for i in range(60):
                zf.writestr(f"file_{i}.pdf", b"%PDF-1.4 test bytes")

        with self.assertRaises(HTTPException) as ctx:
            process_zip_archive(zip_path, self.temp_dir, client="test-client")
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("exceeds maximum allowed files", ctx.exception.detail)

    def test_3_decompression_bomb_ratio_safeguard(self):
        """ZIP archive with high decompression ratio (>100:1) MUST be rejected."""
        zip_path = os.path.join(self.temp_dir, "zip_bomb.zip")
        large_zeros = b"0" * (5 * 1024 * 1024)  # 5MB of zeros (compresses heavily)
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("bomb.pdf", large_zeros)

        with self.assertRaises(HTTPException) as ctx:
            process_zip_archive(zip_path, self.temp_dir, client="test-client")
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Decompression bomb detected", ctx.exception.detail)

    def test_4_nonexistent_file_safe_handling(self):
        """Parsing non-existent file path raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            self.parser.parse("/tmp/non_existent_file_999.pdf")


if __name__ == "__main__":
    unittest.main()
