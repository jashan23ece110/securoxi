"""
SECUROXI AI Core Models & Data Structures
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


class Severity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Verdict(str, Enum):
    SAFE = "SAFE"
    SUSPICIOUS = "SUSPICIOUS"
    HIGH_RISK = "HIGH_RISK"


class AnalysisStatus(str, Enum):
    ANALYZED = "ANALYZED"
    ANALYZED_WITH_OCR = "ANALYZED_WITH_OCR"
    PARTIALLY_ANALYZED = "PARTIALLY_ANALYZED"
    UNINSPECTABLE = "UNINSPECTABLE"


class AttackCategory(str, Enum):
    MICRO_TEXT = "MICRO_TEXT"
    WHITE_TEXT = "WHITE_TEXT"
    BACKGROUND_MATCH = "BACKGROUND_MATCH"
    HIDDEN_TEXT = "HIDDEN_TEXT"
    INVISIBLE_UNICODE = "INVISIBLE_UNICODE"
    SUSPICIOUS_POSITION = "SUSPICIOUS_POSITION"
    VISUAL_DECEPTION = "VISUAL_DECEPTION"
    INSTRUCTION_OVERRIDE = "INSTRUCTION_OVERRIDE"
    SYSTEM_PROMPT_MANIPULATION = "SYSTEM_PROMPT_MANIPULATION"
    ATS_MANIPULATION = "ATS_MANIPULATION"
    AI_ROLE_MANIPULATION = "AI_ROLE_MANIPULATION"
    DATA_EXFILTRATION = "DATA_EXFILTRATION"
    TOOL_MANIPULATION = "TOOL_MANIPULATION"
    OBFUSCATION_INDICATORS = "OBFUSCATION_INDICATORS"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    OBFUSCATION = "OBFUSCATION"
    UNINSPECTABLE_CONTENT = "UNINSPECTABLE_CONTENT"


@dataclass
class TextSpan:
    """Represents a discrete element of text extracted from a document with layout & style metadata."""
    text: str
    page: int = 1
    font_name: Optional[str] = None
    font_size: Optional[float] = None
    font_color: Optional[str] = None  # Hex format e.g., "#FFFFFF" or RGB tuple string
    bg_color: Optional[str] = None    # Hex format e.g., "#FFFFFF" or RGB tuple string
    is_hidden: bool = False           # Document level hidden flag (e.g. w:vanish in docx, display:none in HTML)
    opacity: Optional[float] = 1.0
    bbox: Optional[List[float]] = None # [x0, y0, x1, y1] coordinates
    source: str = "NATIVE_PDF"         # "NATIVE_PDF" or "OCR"
    ocr_confidence: Optional[float] = None # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def page_number(self) -> int:
        return self.page

    def bbox_str(self) -> str:
        if not self.bbox:
            return "N/A"
        return f"({self.bbox[0]}, {self.bbox[1]}, {self.bbox[2]}, {self.bbox[3]})"


@dataclass
class SecurityFinding:
    """Represents a specific security vulnerability or suspicious element detected in a document."""
    finding_id: str
    category: AttackCategory
    severity: Severity
    title: str
    description: str
    evidence: str
    location: Optional[str] = None    # e.g., "Page 1, line 14" or "Span #12"
    confidence: float = 1.0           # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, category: AttackCategory, severity: Severity, title: str, description: str, evidence: str, location: Optional[str] = None, confidence: float = 1.0, metadata: Optional[Dict[str, Any]] = None) -> 'SecurityFinding':
        import uuid
        prefix = category.value[:2] if hasattr(category, "value") else str(category)[:2]
        fid = f"{prefix}-{uuid.uuid4().hex[:8]}"
        return cls(
            finding_id=fid,
            category=category,
            severity=severity,
            title=title,
            description=description,
            evidence=evidence,
            location=location,
            confidence=confidence,
            metadata=metadata or {}
        )


@dataclass
class AnalysisReport:
    """Consolidated report output produced after document analysis."""
    filename: str
    document_type: str
    verdict: Verdict
    risk_score: int = 0
    primary_threat: Optional[str] = None
    overall_confidence: float = 1.0
    verdict_explanation: str = "Document analyzed successfully."
    analysis_status: AnalysisStatus = AnalysisStatus.ANALYZED
    extraction_sources: List[str] = field(default_factory=lambda: ["NATIVE_PDF"])
    correlated_evidence: List[str] = field(default_factory=list)
    findings: List[SecurityFinding] = field(default_factory=list)
    attack_chains: List[Dict[str, Any]] = field(default_factory=list)
    evidence_items: List[Dict[str, Any]] = field(default_factory=list)
    top_contributing_evidence: List[Dict[str, Any]] = field(default_factory=list)

    total_spans_analyzed: int = 0
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __iter__(self):
        yield self.verdict
        yield self.risk_score
        yield self.primary_threat
        yield self.overall_confidence
        yield self.verdict_explanation
        yield self.correlated_evidence

    def to_dict(self) -> Dict[str, Any]:
        """Convert the report into a JSON-serializable dictionary."""
        return {
            "filename": self.filename,
            "document_type": self.document_type,
            "verdict": self.verdict.value,
            "risk_score": self.risk_score,
            "primary_threat": self.primary_threat,
            "overall_confidence": round(self.overall_confidence, 2),
            "verdict_explanation": self.verdict_explanation,
            "analysis_status": self.analysis_status.value if hasattr(self.analysis_status, "value") else str(self.analysis_status),
            "extraction_sources": self.extraction_sources,
            "correlated_evidence": self.correlated_evidence,
            "attack_chains": self.attack_chains,
            "top_contributing_evidence": self.top_contributing_evidence,
            "findings_count": len(self.findings),
            "findings": [
                {
                    "finding_id": f.finding_id,
                    "category": f.category.value if hasattr(f.category, "value") else str(f.category),
                    "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
                    "title": f.title,
                    "description": f.description,
                    "evidence": f.evidence,
                    "location": f.location,
                    "confidence": f.confidence,
                    "metadata": f.metadata
                }
                for f in self.findings
            ],
            "evidence_items": self.evidence_items,
            "total_spans_analyzed": self.total_spans_analyzed,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "metadata": self.metadata
        }
