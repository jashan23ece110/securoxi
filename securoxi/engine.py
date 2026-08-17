"""
SECUROXI AI Core Security Engine
Orchestrates document parsing, security analyzers, and risk correlation.
Hardened for safe failure, structured logging, correlation IDs, and timing metrics.
"""

import time
import os
import uuid
from typing import List, Optional, Dict, Any
from securoxi.config import SecuroxiConfig
from securoxi.logger import get_logger
from securoxi.models import (
    AnalysisReport,
    SecurityFinding,
    Verdict,
    Severity,
    AttackCategory,
    TextSpan
)
from securoxi.parsers.pdf_parser import PDFParser
from securoxi.analyzers.visual_deception import VisualDeceptionAnalyzer
from securoxi.analyzers.prompt_injection import PromptInjectionAnalyzer
from securoxi.risk_engine import SecuroxiRiskEngine
from securoxi.reasoning.service import SecuroxiReasoningService


class SecuroxiEngine:
    """
    Modular deterministic security engine for SECUROXI AI.
    Analyzes documents to detect prompt injection, visual deception, and hidden text.
    Hardened for fail-safe operation, path traversal protection, and resource limits.
    """

    def __init__(self, config: Optional[SecuroxiConfig] = None):
        self.config = config or SecuroxiConfig()
        self.logger = get_logger("securoxi.engine")
        self.parsers = {}
        self.analyzers = []
        self.risk_engine = SecuroxiRiskEngine(config=self.config)
        self.reasoning_service = SecuroxiReasoningService(config=self.config)

        # Register default parsers and analyzers with config
        from securoxi.parsers.docx_parser import DOCXParser
        from securoxi.parsers.txt_parser import TXTParser
        from securoxi.parsers.html_parser import SecuroxiHTMLParser
        from securoxi.parsers.image_parser import ImageOCRParser

        self.register_parser(".pdf", PDFParser(config=self.config))
        self.register_parser(".docx", DOCXParser(config=self.config))
        self.register_parser(".txt", TXTParser(config=self.config))
        self.register_parser(".html", SecuroxiHTMLParser(config=self.config))
        self.register_parser(".htm", SecuroxiHTMLParser(config=self.config))
        self.register_parser(".png", ImageOCRParser(config=self.config))
        self.register_parser(".jpg", ImageOCRParser(config=self.config))
        self.register_parser(".jpeg", ImageOCRParser(config=self.config))

        self.register_analyzer(VisualDeceptionAnalyzer(config=self.config))
        self.register_analyzer(PromptInjectionAnalyzer(config=self.config))

    def register_parser(self, file_extension: str, parser_instance_or_class):
        """Register a document parser for a specific file extension (e.g. '.pdf', '.docx')."""
        if isinstance(parser_instance_or_class, type):
            self.parsers[file_extension.lower()] = parser_instance_or_class(config=self.config)
        else:
            self.parsers[file_extension.lower()] = parser_instance_or_class

    def register_analyzer(self, analyzer_instance):
        """Register a deterministic security analyzer."""
        self.analyzers.append(analyzer_instance)

    def analyze_document(self, file_path: str) -> AnalysisReport:
        """
        Main analysis pipeline:
        1. Validate file path security, canonical resolution, and extension.
        2. Execute parser to extract TextSpans safely (measure parsing_latency_ms).
        3. Pass TextSpans through security analyzers (measure analyzer latencies).
        4. Evaluate Risk Correlation & Verdict Engine.
        5. Pass to AI Security Reasoning Layer if enabled.
        """
        start_scan_time = time.time()
        scan_id = f"SCAN-{uuid.uuid4().hex[:10]}"
        self.logger.info(f"[{scan_id}] Received document scan request for: '{os.path.basename(file_path)}'")

        # 1. Path Safety & Canonical Resolution
        try:
            canonical_path = os.path.abspath(os.path.realpath(file_path))
        except Exception as err:
            self.logger.error(f"[{scan_id}] Unsafe or invalid file path '{file_path}': {err}")
            return self._build_error_report(file_path, "PATH_TRAVERSAL_OR_INVALID_PATH", f"Invalid path: {err}", scan_id=scan_id)

        if not os.path.exists(canonical_path) or not os.path.isfile(canonical_path):
            self.logger.error(f"[{scan_id}] Document file not found: '{canonical_path}'")
            return self._build_error_report(file_path, "FILE_NOT_FOUND", f"File does not exist: {file_path}", scan_id=scan_id)

        filename = os.path.basename(canonical_path)
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        parser = self.parsers.get(ext)
        if not parser:
            self.logger.warning(f"[{scan_id}] Unsupported file format '{ext}' requested for file '{filename}'")
            return self._build_error_report(
                filename,
                "UNSUPPORTED_FORMAT",
                f"Unsupported file format '{ext}'. Supported extensions: {list(self.parsers.keys())}",
                doc_type="UNKNOWN",
                scan_id=scan_id
            )

        # 2. Parse Document into TextSpans
        t0_parse = time.time()
        try:
            self.logger.info(f"[{scan_id}] Executing parser for '{filename}' ({ext})")
            spans: List[TextSpan] = parser.parse(canonical_path)
        except Exception as parse_err:
            self.logger.error(f"[{scan_id}] Parser failure on '{filename}': {str(parse_err)}")
            return self._build_error_report(
                filename,
                "PARSER_FAILURE",
                f"Document parsing failed: {str(parse_err)}",
                doc_type=ext.lstrip('.').upper(),
                scan_id=scan_id
            )
        parsing_latency_ms = round((time.time() - t0_parse) * 1000, 2)

        # 3. Run security analyzers safely
        findings: List[SecurityFinding] = []
        visual_latency_ms = 0.0
        prompt_latency_ms = 0.0

        for analyzer in self.analyzers:
            analyzer_name = analyzer.__class__.__name__
            t0_analyzer = time.time()
            try:
                self.logger.debug(f"[{scan_id}] Running analyzer {analyzer_name} over {len(spans)} spans")
                detected = analyzer.analyze(spans, file_path=canonical_path)
                findings.extend(detected)
            except Exception as analyzer_err:
                self.logger.error(f"[{scan_id}] Analyzer '{analyzer_name}' error: {analyzer_err}. Continuing scan.")
            
            elapsed = round((time.time() - t0_analyzer) * 1000, 2)
            if "Visual" in analyzer_name:
                visual_latency_ms = elapsed
            else:
                prompt_latency_ms = elapsed

        # 4. Evaluate Risk Correlation & Final Verdict
        execution_time_ms = round((time.time() - start_scan_time) * 1000, 2)
        report = self.risk_engine.evaluate(
            findings=findings,
            filename=filename,
            doc_type=ext.lstrip('.').upper(),
            total_spans=len(spans),
            execution_time_ms=execution_time_ms
        )

        # Determine extraction sources and analysis status
        from securoxi.models import AnalysisStatus
        sources = list(set(getattr(s, "source", "NATIVE_PDF") for s in spans)) if spans else []
        if not sources:
            sources = ["NONE"]

        report.extraction_sources = sources

        if len(spans) == 0:
            report.analysis_status = AnalysisStatus.UNINSPECTABLE
            report.verdict = Verdict.SUSPICIOUS
            report.risk_score = max(report.risk_score, 40)
            report.primary_threat = "UNINSPECTABLE_DOCUMENT"
            report.verdict_explanation = "UNINSPECTABLE DOCUMENT WARNING: Document contained no readable text or inspectable visual elements after native extraction and OCR fallback attempts. Quarantined as suspicious for manual security review."
            uninspectable_finding = SecurityFinding.create(
                category=AttackCategory.UNINSPECTABLE_CONTENT,
                severity=Severity.MEDIUM,
                title="Uninspectable Document Content",
                description="The security engine was unable to extract inspectable text or layout elements from this document.",
                evidence="ZERO_EXTRACTED_SPANS",
                location="Document Level",
                confidence=1.0
            )
            report.findings.append(uninspectable_finding)
        elif "OCR" in sources and "NATIVE_PDF" in sources:
            report.analysis_status = AnalysisStatus.PARTIALLY_ANALYZED
        elif "OCR" in sources:
            report.analysis_status = AnalysisStatus.ANALYZED_WITH_OCR
        else:
            report.analysis_status = AnalysisStatus.ANALYZED

        # 5. Execute Stage 3 AI Security Reasoning Layer
        t0_ai = time.time()
        document_text_context = " ".join(s.text for s in spans)
        report = self.reasoning_service.evaluate_report(report, document_text_context=document_text_context)
        ai_reasoning_latency_ms = round((time.time() - t0_ai) * 1000, 2)

        total_scan_latency_ms = round((time.time() - start_scan_time) * 1000, 2)

        # Record timing metrics & scan_id correlation ID in report metadata
        report.metadata["scan_id"] = scan_id
        report.metadata["analysis_status"] = report.analysis_status.value if hasattr(report.analysis_status, "value") else str(report.analysis_status)
        report.metadata["extraction_sources"] = report.extraction_sources
        report.metadata["timing_ms"] = {
            "parsing_latency_ms": parsing_latency_ms,
            "visual_analyzer_latency_ms": visual_latency_ms,
            "prompt_analyzer_latency_ms": prompt_latency_ms,
            "ai_reasoning_latency_ms": ai_reasoning_latency_ms,
            "total_scan_latency_ms": total_scan_latency_ms
        }

        self.logger.info(f"[{scan_id}] Scan complete for '{filename}': Verdict={report.verdict.value}, Score={report.risk_score}/100, Status={report.analysis_status.value}, TotalTime={total_scan_latency_ms}ms")
        return report

    def _build_error_report(
        self,
        filename: str,
        error_code: str,
        error_message: str,
        doc_type: str = "UNKNOWN",
        scan_id: str = "SCAN-ERR"
    ) -> AnalysisReport:
        """Helper to build a fail-safe AnalysisReport when parsing or validation fails."""
        from securoxi.models import AnalysisStatus
        finding = SecurityFinding(
            finding_id=f"ERR-{uuid.uuid4().hex[:8]}",
            category=AttackCategory.UNINSPECTABLE_CONTENT,
            severity=Severity.HIGH,
            title=f"Scan Failure ({error_code})",
            description=error_message,
            evidence=error_code,
            location="Document Level",
            confidence=1.0,
            metadata={"error_code": error_code}
        )

        return AnalysisReport(
            filename=os.path.basename(filename),
            document_type=doc_type,
            verdict=Verdict.SUSPICIOUS,
            risk_score=40,
            primary_threat="DOCUMENT_PARSE_ERROR",
            overall_confidence=1.0,
            verdict_explanation=f"DOCUMENT SCAN WARNING: Could not analyze file safely ({error_code}). {error_message}",
            analysis_status=AnalysisStatus.UNINSPECTABLE,
            extraction_sources=["NONE"],
            findings=[finding],
            total_spans_analyzed=0,
            execution_time_ms=0.0,
            metadata={"error_code": error_code, "scan_id": scan_id}
        )
