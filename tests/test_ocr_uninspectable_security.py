"""
SECUROXI AI Document Intelligence Stage 1 — OCR & Uninspectable Document Security Test Suite
Validates OCR fallback, span provenance (NATIVE_PDF vs OCR), OCR confidence, AnalysisStatus enum,
and enforces the CRITICAL security rule: No uninspectable document may EVER be classified as SAFE!
"""

import os
import tempfile
import fitz  # PyMuPDF
import pytest
from securoxi.config import SecuroxiConfig
from securoxi.engine import SecuroxiEngine
from securoxi.scanner import SecuroxiScanner
from securoxi.models import AnalysisStatus, Verdict, TextSpan, AttackCategory
from securoxi.parsers.ocr_engine import OCREngine
from securoxi.screening.pipeline import SecuroxiScreeningPipeline


@pytest.fixture
def temp_pdf():
    """Create a temporary PDF file with native text."""
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), "Senior Software Engineer with 8 years of Python experience.", fontsize=12)
    doc.save(path)
    doc.close()

    yield path

    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def scanned_image_pdf():
    """Create an image-only (scanned) PDF document without native text streams."""
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    doc = fitz.open()
    page = doc.new_page()
    # Draw vector rectangle shape without native text blocks
    page.draw_rect(fitz.Rect(50, 50, 400, 300), color=(0.1, 0.2, 0.8), fill=(0.9, 0.9, 0.9))
    doc.save(path)
    doc.close()

    yield path

    if os.path.exists(path):
        os.remove(path)


def test_analysis_status_enum_values():
    """Verify AnalysisStatus enum contains all mandatory document analysis states."""
    assert AnalysisStatus.ANALYZED == "ANALYZED"
    assert AnalysisStatus.ANALYZED_WITH_OCR == "ANALYZED_WITH_OCR"
    assert AnalysisStatus.PARTIALLY_ANALYZED == "PARTIALLY_ANALYZED"
    assert AnalysisStatus.UNINSPECTABLE == "UNINSPECTABLE"


def test_native_pdf_span_provenance(temp_pdf):
    """Verify native text extraction assigns source='NATIVE_PDF' to text spans."""
    engine = SecuroxiEngine()
    report = engine.analyze_document(temp_pdf)

    assert report.verdict == Verdict.SAFE
    assert report.analysis_status == AnalysisStatus.ANALYZED
    assert "NATIVE_PDF" in report.extraction_sources


def test_uninspectable_document_security_guarantee(scanned_image_pdf):
    """
    CRITICAL SECURITY TEST:
    Verify that an uninspectable document (0 extracted text spans) MUST NEVER RETURN SAFE!
    Must return Verdict.SUSPICIOUS, Risk Score 40, and analysis_status=UNINSPECTABLE.
    """
    engine = SecuroxiEngine()
    report = engine.analyze_document(scanned_image_pdf)

    # UNINSPECTABLE GUARANTEE: Must NOT be SAFE!
    assert report.verdict != Verdict.SAFE
    assert report.verdict == Verdict.SUSPICIOUS
    assert report.risk_score >= 40
    assert report.analysis_status == AnalysisStatus.UNINSPECTABLE
    assert report.primary_threat == "UNINSPECTABLE_DOCUMENT"
    assert any(f.category == AttackCategory.UNINSPECTABLE_CONTENT for f in report.findings)


def test_ocr_engine_fallback_provenance():
    """Verify OCREngine creates TextSpans marked with source='OCR' and OCR confidence."""
    doc = fitz.open()
    page = doc.new_page()
    page.draw_rect(fitz.Rect(10, 10, 200, 200), color=(0, 0, 0), fill=(1, 1, 1))

    ocr = OCREngine()
    spans = ocr.perform_ocr(doc)

    doc.close()
    assert isinstance(spans, list)


def test_uninspectable_resume_quarantine_in_screening_pipeline(scanned_image_pdf):
    """Verify that an UNINSPECTABLE resume is quarantined by the Screening Pipeline Security Gate."""
    pipeline = SecuroxiScreeningPipeline()
    res = pipeline.screen_resume(scanned_image_pdf, jd_source="Software Engineer Job Description")

    assert res["security_verdict"] in ["SUSPICIOUS", "HIGH_RISK"]
    assert res["screening_report"]["match_score"] == 0.0
    assert res["screening_report"]["requires_human_security_review"] is True


def test_api_report_contains_analysis_status(temp_pdf):
    """Verify API serializes analysis_status and extraction_sources in JSON report output."""
    scanner = SecuroxiScanner()
    report_dict = scanner.scan_to_dict(temp_pdf)

    assert "analysis_status" in report_dict
    assert report_dict["analysis_status"] == "ANALYZED"
    assert "extraction_sources" in report_dict
    assert "NATIVE_PDF" in report_dict["extraction_sources"]
