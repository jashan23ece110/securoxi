"""
SECUROXI AI Phase 2 Stage 1 — Ingestion Engine
Reuses Phase 1 secure parsing infrastructure to ingest and structure Resumes and Job Descriptions.
"""

import os
import uuid
import re
from typing import List, Dict, Any, Optional, Union
from securoxi.config import SecuroxiConfig
from securoxi.logger import get_logger
from securoxi.scanner import SecuroxiScanner
from securoxi.parsers.pdf_parser import PDFParser
from securoxi.models import TextSpan, AnalysisReport, Verdict
from securoxi.screening.models import (
    IngestionDocType,
    DocumentMetadata,
    DocumentSection,
    ResumeDocument,
    JobDescriptionDocument
)


class SecuroxiIngestionEngine:
    """
    Ingestion Engine for Phase 2 Resume-to-JD Screening.
    Enforces Phase 1 Security Pipeline on all Resume inputs before downstream structuring.
    """

    def __init__(self, config: Optional[SecuroxiConfig] = None):
        self.config = config or SecuroxiConfig()
        self.logger = get_logger("securoxi.screening.ingestion")
        self.scanner = SecuroxiScanner(config=self.config)
        self.pdf_parser = PDFParser(config=self.config)

    def ingest_resume(self, file_path: str) -> ResumeDocument:
        """
        Ingest an untrusted Resume document.
        1. Validates file path and resource boundaries.
        2. Executes Phase 1 Security Pipeline (Security Scan).
        3. Parses layout spans and extracts structured document sections.
        """
        self.logger.info(f"Ingesting Resume document: '{file_path}'")
        
        # 1. Validate File Path
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            raise FileNotFoundError(f"Resume document not found at: '{file_path}'")

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError(f"Resume document '{file_path}' is empty (0 bytes).")

        filename = os.path.basename(file_path)
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        supported_exts = [".pdf", ".docx", ".txt", ".html", ".htm", ".png", ".jpg", ".jpeg"]
        if ext not in supported_exts:
            raise ValueError(f"Unsupported resume file format '{ext}'. Supported formats: {supported_exts}")

        # 2. Execute Phase 1 Security Pipeline Scan
        security_report: AnalysisReport = self.scanner.scan(file_path)

        # 3. Parse Spans using unified parser registry
        parser = self.scanner.engine.parsers.get(ext, self.pdf_parser)
        spans: List[TextSpan] = parser.parse(file_path)
        raw_text = "\n".join(s.text for s in spans)
        norm_text = raw_text.lower()

        # 4. Extract Structured Resume Sections
        sections = self._partition_resume_sections(spans)

        max_page = max((s.page for s in spans), default=1)
        doc_meta = DocumentMetadata(
            filename=filename,
            file_format="PDF",
            doc_type=IngestionDocType.RESUME,
            file_size_bytes=file_size,
            page_count=max_page,
            total_spans=len(spans),
            security_verdict=security_report.verdict,
            security_risk_score=security_report.risk_score
        )

        resume_id = f"RES-{uuid.uuid4().hex[:8]}"

        return ResumeDocument(
            resume_id=resume_id,
            metadata=doc_meta,
            raw_text=raw_text,
            normalized_text=norm_text,
            sections=sections,
            security_report=security_report,
            extracted_spans=spans
        )

    def ingest_job_description(self, source: Union[str, Dict[str, Any]]) -> JobDescriptionDocument:
        """
        Ingest a Job Description (from file path or raw text string).
        """
        self.logger.info("Ingesting Job Description document")

        if isinstance(source, str) and os.path.isfile(source):
            filename = os.path.basename(source)
            file_size = os.path.getsize(source)
            if file_size == 0:
                raise ValueError(f"Job Description file '{source}' is empty (0 bytes).")

            _, ext = os.path.splitext(filename)
            if ext.lower() == ".pdf":
                spans = self.pdf_parser.parse(source)
                raw_text = "\n".join(s.text for s in spans)
            else:
                with open(source, "r", encoding="utf-8", errors="ignore") as f:
                    raw_text = f.read()
                spans = []
        elif isinstance(source, str):
            filename = "raw_jd_text.txt"
            file_size = len(source.encode("utf-8"))
            if file_size == 0:
                raise ValueError("Job Description text input is empty.")
            raw_text = source
            spans = []
        else:
            raise ValueError("Invalid Job Description source input.")

        norm_text = raw_text.lower()
        sections = self._partition_jd_sections(raw_text)

        # Infer job title
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        job_title = lines[0] if lines else "Job Position"

        doc_meta = DocumentMetadata(
            filename=filename,
            file_format="TXT/PDF",
            doc_type=IngestionDocType.JOB_DESCRIPTION,
            file_size_bytes=file_size,
            page_count=1,
            total_spans=len(spans),
            security_verdict=Verdict.SAFE,
            security_risk_score=0
        )

        jd_id = f"JD-{uuid.uuid4().hex[:8]}"

        return JobDescriptionDocument(
            jd_id=jd_id,
            metadata=doc_meta,
            job_title=job_title,
            raw_text=raw_text,
            normalized_text=norm_text,
            sections=sections,
            extracted_spans=spans
        )

    def _partition_resume_sections(self, spans: List[TextSpan]) -> List[DocumentSection]:
        """Partitions resume text spans into logical sections (Experience, Education, Skills, etc.)."""
        section_headers = ["SUMMARY", "EXPERIENCE", "WORK EXPERIENCE", "EDUCATION", "SKILLS", "PROJECTS", "CERTIFICATIONS"]
        sections: List[DocumentSection] = []

        current_heading = "HEADER"
        current_lines: List[str] = []
        current_start_page = 1

        for span in spans:
            text_strip = span.text.strip().upper()
            matched_header = next((h for h in section_headers if h in text_strip), None)

            if matched_header and len(span.text.strip()) < 40:
                if current_lines:
                    sections.append(DocumentSection(
                        heading=current_heading,
                        text_content="\n".join(current_lines),
                        start_page=current_start_page,
                        end_page=span.page,
                        spans_count=len(current_lines)
                    ))
                current_heading = matched_header
                current_lines = [span.text]
                current_start_page = span.page
            else:
                current_lines.append(span.text)

        if current_lines:
            sections.append(DocumentSection(
                heading=current_heading,
                text_content="\n".join(current_lines),
                start_page=current_start_page,
                end_page=current_start_page,
                spans_count=len(current_lines)
            ))

        return sections

    def _partition_jd_sections(self, raw_text: str) -> List[DocumentSection]:
        """Partitions job description text into logical sections."""
        section_headers = ["OVERVIEW", "RESPONSIBILITIES", "REQUIREMENTS", "QUALIFICATIONS", "BENEFITS"]
        sections: List[DocumentSection] = []

        current_heading = "TITLE_OVERVIEW"
        current_lines: List[str] = []

        for line in raw_text.splitlines():
            line_upper = line.strip().upper()
            matched_header = next((h for h in section_headers if h in line_upper), None)

            if matched_header and len(line.strip()) < 40:
                if current_lines:
                    sections.append(DocumentSection(
                        heading=current_heading,
                        text_content="\n".join(current_lines),
                        start_page=1,
                        end_page=1,
                        spans_count=len(current_lines)
                    ))
                current_heading = matched_header
                current_lines = [line]
            else:
                current_lines.append(line)

        if current_lines:
            sections.append(DocumentSection(
                heading=current_heading,
                text_content="\n".join(current_lines),
                start_page=1,
                end_page=1,
                spans_count=len(current_lines)
            ))

        return sections
