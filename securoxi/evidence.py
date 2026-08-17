"""
SECUROXI AI Advanced Evidence & Risk Engine
Structured evidence data models, attack chain representation, evidence grouping,
and traceability breakdown.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from securoxi.models import SecurityFinding, AttackCategory, Severity


@dataclass
class EvidenceItem:
    """
    Rich, traceable evidence item capturing original text, normalized text,
    location, formatting metadata, analyzer source, and impact score.
    """
    evidence_id: str
    category: AttackCategory
    severity: Severity
    title: str
    description: str
    original_text: str
    normalized_text: str
    page: int
    bbox: Optional[List[float]]
    location: str
    formatting_metadata: Dict[str, Any]
    analyzer_source: str
    ai_reasoning_source: Optional[str] = None
    confidence_weight: float = 0.95
    impact_score: int = 25

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "category": self.category.value if hasattr(self.category, "value") else str(self.category),
            "severity": self.severity.value if hasattr(self.severity, "value") else str(self.severity),
            "title": self.title,
            "description": self.description,
            "original_text": self.original_text,
            "normalized_text": self.normalized_text,
            "page": self.page,
            "bbox": self.bbox,
            "location": self.location,
            "formatting_metadata": self.formatting_metadata,
            "analyzer_source": self.analyzer_source,
            "ai_reasoning_source": self.ai_reasoning_source,
            "confidence_weight": round(self.confidence_weight, 2),
            "impact_score": self.impact_score
        }


@dataclass
class AttackChain:
    """
    Represents a correlated multi-stage or compound attack chain combining
    visual deception, instruction overrides, or candidate ranking manipulation.
    """
    chain_id: str
    title: str
    description: str
    contributing_categories: List[str]
    evidence_ids: List[str]
    severity: Severity
    risk_boost: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "title": self.title,
            "description": self.description,
            "contributing_categories": self.contributing_categories,
            "evidence_ids": self.evidence_ids,
            "severity": self.severity.value if hasattr(self.severity, "value") else str(self.severity),
            "risk_boost": self.risk_boost
        }


@dataclass
class EvidenceGroup:
    """Group of evidence items linked by location proximity (same span, nearby spans, same page)."""
    group_type: str  # "same_span", "nearby_spans", "same_page"
    location_key: str
    items: List[EvidenceItem] = field(default_factory=list)


class EvidenceAggregator:
    """
    Aggregates security findings into structured evidence items, groups evidence by proximity,
    synthesizes multi-finding attack chains, and computes top contributing evidence.
    """

    def __init__(self, category_weights: Optional[Dict[AttackCategory, int]] = None):
        self.category_weights = category_weights or {}

    def build_evidence_items(self, findings: List[SecurityFinding]) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []
        for idx, f in enumerate(findings, 1):
            category_val = f.category.value if hasattr(f.category, "value") else str(f.category)
            meta = f.metadata or {}
            orig_text = meta.get("original_text", f.evidence)
            norm_text = meta.get("normalized_text", orig_text.lower() if orig_text else "")
            
            # Extract page from location string or metadata
            page = 1
            if "Page " in (f.location or ""):
                try:
                    page_part = f.location.split(",")[0].replace("Page ", "").strip()
                    page = int(page_part)
                except ValueError:
                    page = 1

            bbox = meta.get("bbox")
            font_size = meta.get("font_size")
            font_color = meta.get("font_color")
            formatting_meta = {
                "font_size": font_size,
                "font_color": font_color,
                "bg_color": meta.get("bg_color"),
                "is_hidden": meta.get("is_hidden", False)
            }

            weight = self.category_weights.get(f.category, 25)
            analyzer_name = "VisualDeceptionAnalyzer" if "VD-" in f.finding_id or category_val in [
                "MICRO_TEXT", "WHITE_TEXT", "BACKGROUND_MATCH", "HIDDEN_TEXT", "INVISIBLE_UNICODE", "SUSPICIOUS_POSITION"
            ] else "PromptInjectionAnalyzer"

            item = EvidenceItem(
                evidence_id=f.finding_id or f"EVD-{idx:03d}",
                category=f.category,
                severity=f.severity,
                title=f.title,
                description=f.description,
                original_text=orig_text,
                normalized_text=norm_text,
                page=page,
                bbox=bbox,
                location=f.location or f"Page {page}",
                formatting_metadata=formatting_meta,
                analyzer_source=analyzer_name,
                confidence_weight=f.confidence,
                impact_score=weight
            )
            items.append(item)
        return items

    def group_evidence(self, items: List[EvidenceItem]) -> Dict[str, List[EvidenceItem]]:
        """Group evidence items by page number and location."""
        grouped: Dict[str, List[EvidenceItem]] = {}
        for item in items:
            key = f"Page_{item.page}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(item)
        return grouped

    def synthesize_attack_chains(self, items: List[EvidenceItem]) -> List[AttackChain]:
        """Synthesize compound multi-stage attack chains from evidence items."""
        chains: List[AttackChain] = []
        if not items:
            return chains

        categories_present = {item.category for item in items}
        ev_ids = [item.evidence_id for item in items]

        has_visual = any(c in categories_present for c in [
            AttackCategory.MICRO_TEXT, AttackCategory.WHITE_TEXT, AttackCategory.HIDDEN_TEXT, AttackCategory.INVISIBLE_UNICODE
        ])
        has_ats = AttackCategory.ATS_MANIPULATION in categories_present
        has_override = AttackCategory.INSTRUCTION_OVERRIDE in categories_present
        has_exfil = AttackCategory.DATA_EXFILTRATION in categories_present

        if has_visual and has_ats:
            chains.append(AttackChain(
                chain_id="CHAIN-001",
                title="Concealed Candidate Ranking Manipulation Chain",
                description="Visually concealed content (micro/white text) attempts to manipulate automated ATS candidate scoring and ranking.",
                contributing_categories=["WHITE_TEXT / MICRO_TEXT", "ATS_MANIPULATION"],
                evidence_ids=ev_ids[:2],
                severity=Severity.CRITICAL,
                risk_boost=25
            ))

        if has_visual and has_override:
            chains.append(AttackChain(
                chain_id="CHAIN-002",
                title="Hidden System Instruction Override Chain",
                description="Visually hidden text contains direct directives attempting to override or negate system prompts.",
                contributing_categories=["VISUAL_DECEPTION", "INSTRUCTION_OVERRIDE"],
                evidence_ids=ev_ids[:2],
                severity=Severity.HIGH,
                risk_boost=20
            ))

        if has_visual and has_exfil:
            chains.append(AttackChain(
                chain_id="CHAIN-003",
                title="Stealth Data Exfiltration Chain",
                description="Concealed text span contains directives to extract or exfiltrate system secrets and API keys.",
                contributing_categories=["HIDDEN_TEXT", "DATA_EXFILTRATION"],
                evidence_ids=ev_ids[:2],
                severity=Severity.CRITICAL,
                risk_boost=25
            ))

        return chains

    def get_top_contributing_evidence(self, items: List[EvidenceItem], limit: int = 3) -> List[EvidenceItem]:
        """Return the top N evidence items contributing most to final risk score."""
        sorted_items = sorted(items, key=lambda item: (item.impact_score * item.confidence_weight), reverse=True)
        return sorted_items[:limit]
