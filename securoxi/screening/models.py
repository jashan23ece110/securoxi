"""
SECUROXI AI Phase 2 Stage 1 — Resume & Job Description Domain Models
Defines structured document representations for Resume and Job Description ingestion.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from securoxi.models import AnalysisReport, TextSpan, Verdict


class IngestionDocType(str, Enum):
    RESUME = "RESUME"
    JOB_DESCRIPTION = "JOB_DESCRIPTION"


@dataclass
class DocumentMetadata:
    """Metadata tracking file properties, type classification, and security verdict."""
    filename: str
    file_format: str
    doc_type: IngestionDocType
    file_size_bytes: int
    page_count: int
    total_spans: int
    security_verdict: Verdict = Verdict.SAFE
    security_risk_score: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filename": self.filename,
            "file_format": self.file_format,
            "doc_type": self.doc_type.value,
            "file_size_bytes": self.file_size_bytes,
            "page_count": self.page_count,
            "total_spans": self.total_spans,
            "security_verdict": self.security_verdict.value,
            "security_risk_score": self.security_risk_score,
            "metadata": self.metadata
        }


@dataclass
class DocumentSection:
    """Structured document section representation with layout traceability."""
    heading: str
    text_content: str
    start_page: int = 1
    end_page: int = 1
    spans_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "heading": self.heading,
            "text_content": self.text_content,
            "start_page": self.start_page,
            "end_page": self.end_page,
            "spans_count": self.spans_count,
            "metadata": self.metadata
        }


@dataclass
class ResumeDocument:
    """
    Structured internal representation of an ingested Candidate Resume.
    Preserves Phase 1 security report findings and layout metadata.
    """
    resume_id: str
    metadata: DocumentMetadata
    raw_text: str
    normalized_text: str
    sections: List[DocumentSection] = field(default_factory=list)
    security_report: Optional[AnalysisReport] = None
    extracted_spans: List[TextSpan] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resume_id": self.resume_id,
            "metadata": self.metadata.to_dict(),
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
            "sections": [s.to_dict() for s in self.sections],
            "security_report": self.security_report.to_dict() if self.security_report else None,
            "spans_count": len(self.extracted_spans)
        }


@dataclass
class JobDescriptionDocument:
    """
    Structured internal representation of an ingested Job Description.
    """
    jd_id: str
    metadata: DocumentMetadata
    job_title: str
    raw_text: str
    normalized_text: str
    sections: List[DocumentSection] = field(default_factory=list)
    extracted_spans: List[TextSpan] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "jd_id": self.jd_id,
            "metadata": self.metadata.to_dict(),
            "job_title": self.job_title,
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
            "sections": [s.to_dict() for s in self.sections],
            "spans_count": len(self.extracted_spans)
        }
