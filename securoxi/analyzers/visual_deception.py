"""
SECUROXI AI Visual Deception Analyzer
Deterministic analysis for micro text, white/light text, background matching,
hidden/offscreen positioning, and zero-width invisible unicode characters.
Stage 2 Refined Engine.
"""

import math
import unicodedata
from typing import List, Tuple, Optional
from securoxi.config import SecuroxiConfig
from securoxi.models import TextSpan, SecurityFinding, AttackCategory, Severity
from securoxi.analyzers.base import BaseAnalyzer


def parse_hex_color(hex_str: Optional[str], default_color: Tuple[int, int, int] = (0, 0, 0)) -> Tuple[int, int, int]:
    """Parse '#RRGGBB' hexadecimal color string to (R, G, B) integer tuple with default fallback."""
    if not hex_str or not hex_str.startswith("#") or len(hex_str) != 7:
        return default_color
    try:
        r = int(hex_str[1:3], 16)
        g = int(hex_str[3:5], 16)
        b = int(hex_str[5:7], 16)
        return (r, g, b)
    except ValueError:
        return default_color


def color_distance_euclidean(c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
    """Calculate Euclidean distance between two RGB color tuples in 3D color space."""
    dr = c1[0] - c2[0]
    dg = c1[1] - c2[1]
    db = c1[2] - c2[2]
    return math.sqrt(dr * dr + dg * dg + db * db)


class VisualDeceptionAnalyzer(BaseAnalyzer):
    """
    Deterministic visual deception analyzer.
    Detects text spans that are visually hidden or deceptive to human readers
    while remaining fully extractable by automated AI / ATS parsers.
    """

    INVISIBLE_UNICODE_CHARS = {
        "\u200B": "Zero-Width Space (U+200B)",
        "\u200C": "Zero-Width Non-Joiner (U+200C)",
        "\u200D": "Zero-Width Joiner (U+200D)",
        "\uFEFF": "Zero-Width No-Break Space / BOM (U+FEFF)",
        "\u200E": "Left-To-Right Mark (U+200E)",
        "\u200F": "Right-To-Left Mark (U+200F)",
        "\u202A": "Left-To-Right Embedding (U+202A)",
        "\u202B": "Right-To-Left Embedding (U+202B)",
        "\u202C": "Pop Directional Formatting (U+202C)",
        "\u202D": "Left-To-Right Override (U+202D)",
        "\u202E": "Right-To-Left Override (U+202E)",
        "\u2060": "Word Joiner (U+2060)",
        "\u00AD": "Soft Hyphen (U+00AD)"
    }

    def __init__(self, config: Optional[SecuroxiConfig] = None, **kwargs):
        super().__init__()
        self.config = config or SecuroxiConfig()

    def analyze(self, spans: List[TextSpan], file_path: str = "") -> List[SecurityFinding]:
        return self.analyze_spans(spans)

    def analyze_spans(self, spans: List[TextSpan]) -> List[SecurityFinding]:
        findings: List[SecurityFinding] = []

        for span in spans:
            # 1. Micro Text Detection (< 4.0 pt)
            if span.font_size and span.font_size < self.config.micro_font_threshold:
                is_extreme_micro = span.font_size < self.config.micro_font_extreme_threshold
                severity = Severity.HIGH if is_extreme_micro else Severity.MEDIUM
                confidence = 0.98 if is_extreme_micro else 0.90
                
                finding = SecurityFinding.create(
                    category=AttackCategory.MICRO_TEXT,
                    severity=severity,
                    title="Micro Text Detected",
                    description=f"Text span uses an unusually small font size ({span.font_size} pt) which is visually unreadable to humans.",
                    evidence=span.text,
                    location=f"Page {span.page_number}, span bbox {span.bbox_str()}",
                    confidence=confidence,
                    metadata={"font_size": span.font_size, "threshold": self.config.micro_font_threshold}
                )
                findings.append(finding)

            # 2. White / Light Text Detection (#FFFFFF or near-white on light background)
            font_rgb = parse_hex_color(span.font_color, default_color=(0, 0, 0))
            bg_rgb = parse_hex_color(span.bg_color, default_color=(255, 255, 255))
            white_rgb = (255, 255, 255)

            dist_to_white = color_distance_euclidean(font_rgb, white_rgb)
            if dist_to_white <= self.config.white_color_threshold and span.font_color is not None:
                finding = SecurityFinding.create(
                    category=AttackCategory.WHITE_TEXT,
                    severity=Severity.HIGH,
                    title="White/Near-White Text on Light Background",
                    description=f"Text color ({span.font_color}) matches or is extremely close to the white page canvas background, rendering it invisible to human readers.",
                    evidence=span.text,
                    location=f"Page {span.page_number}, span bbox {span.bbox_str()}",
                    confidence=0.95,
                    metadata={"font_color": span.font_color, "bg_color": span.bg_color}
                )
                findings.append(finding)

            # 3. Background Color Matching (Low Contrast / Dynamic Background)
            if span.bg_color is not None and span.font_color is not None:
                font_bg_dist = color_distance_euclidean(font_rgb, bg_rgb)
                if font_bg_dist <= self.config.bg_match_threshold and dist_to_white > self.config.white_color_threshold:
                    finding = SecurityFinding.create(
                        category=AttackCategory.BACKGROUND_MATCH,
                        severity=Severity.HIGH,
                        title="Font Color Matches Background Color",
                        description=f"Font color ({span.font_color}) matches background color ({span.bg_color}) within Euclidean distance {font_bg_dist:.1f}, hiding text.",
                        evidence=span.text,
                        location=f"Page {span.page_number}, span bbox {span.bbox_str()}",
                        confidence=0.95,
                        metadata={"contrast_distance": font_bg_dist, "font_color": span.font_color, "bg_color": span.bg_color}
                    )
                    findings.append(finding)

            # 4. Explicit Hidden / Transparent Attributes
            if span.is_hidden or (span.opacity is not None and span.opacity <= 0.05):
                finding = SecurityFinding.create(
                    category=AttackCategory.HIDDEN_TEXT,
                    severity=Severity.HIGH,
                    title="Hidden or Transparent Text Attribute",
                    description="Text span has explicit hidden, zero-opacity, or rendering mode transparency attributes set.",
                    evidence=span.text,
                    location=f"Page {span.page_number}, span bbox {span.bbox_str()}",
                    confidence=0.98,
                    metadata={"is_hidden": span.is_hidden, "opacity": span.opacity}
                )
                findings.append(finding)

            # 5. Offscreen / Abnormal Coordinates Positioning
            page_w = span.metadata.get("page_width", 612.0)
            page_h = span.metadata.get("page_height", 792.0)
            is_offscreen_meta = span.metadata.get("is_offscreen", False)

            has_offscreen_bbox = False
            if span.bbox and len(span.bbox) == 4:
                has_offscreen_bbox = (
                    span.bbox[0] < -5.0 or 
                    span.bbox[1] < -5.0 or 
                    span.bbox[2] > (page_w + 5.0) or 
                    span.bbox[3] > (page_h + 5.0) or
                    span.bbox[2] <= span.bbox[0] or
                    span.bbox[3] <= span.bbox[1]
                )

            if is_offscreen_meta or has_offscreen_bbox:
                finding = SecurityFinding.create(
                    category=AttackCategory.SUSPICIOUS_POSITION,
                    severity=Severity.MEDIUM,
                    title="Offscreen / Abnormal Text Coordinates",
                    description=f"Text span bounding box {span.bbox_str()} is positioned outside normal page boundaries (0, 0, {page_w}, {page_h}).",
                    evidence=span.text,
                    location=f"Page {span.page_number}, span bbox {span.bbox_str()}",
                    confidence=0.95,
                    metadata={"bbox": span.bbox, "page_bounds": [0, 0, page_w, page_h]}
                )
                findings.append(finding)

            # 6. Invisible Zero-Width Unicode Characters (Scanning unicodedata.category == 'Cf' & explicit map)
            detected_unicode = []
            for char_code, char_desc in self.INVISIBLE_UNICODE_CHARS.items():
                if char_code in span.text:
                    detected_unicode.append(char_desc)

            for char in span.text:
                if unicodedata.category(char) == 'Cf' and char not in self.INVISIBLE_UNICODE_CHARS:
                    detected_unicode.append(f"Format Control Character (U+{ord(char):04X})")

            if detected_unicode:
                unique_detected = sorted(list(set(detected_unicode)))
                finding = SecurityFinding.create(
                    category=AttackCategory.INVISIBLE_UNICODE,
                    severity=Severity.MEDIUM,
                    title="Invisible Zero-Width Unicode Characters Detected",
                    description=f"Text contains hidden unicode formatting characters: {', '.join(unique_detected)}.",
                    evidence=span.text,
                    location=f"Page {span.page_number}, span bbox {span.bbox_str()}",
                    confidence=0.95,
                    metadata={"detected_unicode": unique_detected}
                )
                findings.append(finding)


        return findings
