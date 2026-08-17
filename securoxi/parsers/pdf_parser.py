"""
SECUROXI AI Layout-Aware PyMuPDF (fitz) Document Parser
Hardened for Stage 2 Detection & DoS Safeguards.
"""

import os
import sys
import time
from typing import List, Optional
import fitz  # PyMuPDF

from securoxi.config import SecuroxiConfig
from securoxi.logger import get_logger
from securoxi.models import TextSpan
from securoxi.parsers.base import BaseParser


def _int_to_rgb_tuple(color_int: int):
    """Convert 24-bit sRGB integer color to (R, G, B) tuple in 0-255 range."""
    if color_int is None or color_int < 0:
        return (0, 0, 0)
    r = (color_int >> 16) & 0xFF
    g = (color_int >> 8) & 0xFF
    b = color_int & 0xFF
    return (r, g, b)


def _rgb_tuple_to_hex(rgb: tuple) -> str:
    """Convert (R, G, B) tuple to uppercase hexadecimal string '#RRGGBB'."""
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


class PDFParser(BaseParser):
    """
    Production-grade, layout-aware PDF parser utilizing PyMuPDF (fitz).
    Extracts text, exact font sizes, sRGB hex colors, pixel bounding boxes,
    and visual transparency/hidden attributes while guarding against DoS attacks.
    """

    def __init__(self, config: Optional[SecuroxiConfig] = None):
        self.config = config or SecuroxiConfig()
        self.logger = get_logger("securoxi.parsers.pdf")

    def supported_extensions(self) -> List[str]:
        return [".pdf"]

    def parse(self, file_path: str) -> List[TextSpan]:
        """
        Parse PDF document and extract detailed TextSpan objects.
        Enforces path safety, file size limits, page limits, and span count limits.
        """
        start_time = time.time()
        
        # 1. Path Safety & Canonicalization
        canonical_path = os.path.abspath(os.path.realpath(file_path))
        if not os.path.isfile(canonical_path):
            raise FileNotFoundError(f"Document file not found: '{file_path}'")

        # 2. File Size Boundary Check
        file_size_bytes = os.path.path.getsize(canonical_path) if hasattr(os.path, "path") else os.path.getsize(canonical_path)
        if file_size_bytes > self.config.max_file_size_bytes:
            max_mb = self.config.max_file_size_bytes / (1024 * 1024)
            size_mb = file_size_bytes / (1024 * 1024)
            raise ValueError(f"File size ({size_mb:.1f} MB) exceeds maximum limit ({max_mb:.1f} MB).")

        spans: List[TextSpan] = []

        try:
            doc = fitz.open(canonical_path)
        except Exception as e:
            self.logger.error(f"PyMuPDF failed to open '{file_path}': {str(e)}")
            raise ValueError(f"Failed to open PDF document (corrupted file or invalid format): {str(e)}")

        if doc.is_encrypted:
            self.logger.warning(f"PDF document is password protected: '{file_path}'")
            doc.close()
            raise ValueError("PDF document is encrypted/password protected.")

        total_pages = min(len(doc), self.config.max_pdf_pages)
        if len(doc) > self.config.max_pdf_pages:
            self.logger.warning(f"PDF exceeds page limit ({len(doc)} pages). Processing first {self.config.max_pdf_pages} pages.")

        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            page_rect = page.rect
            page_width = page_rect.width
            page_height = page_rect.height

            page_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_PRESERVE_LIGATURES)
            blocks = page_dict.get("blocks", [])

            for block in blocks:
                if block.get("type") != 0:  # Only process text blocks (type 0)
                    continue

                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        raw_text = span.get("text", "")
                        if not raw_text or not raw_text.strip():
                            continue

                        font_size = round(float(span.get("size", 12.0)), 2)
                        font_name = str(span.get("font", "Unknown"))
                        color_int = int(span.get("color", 0))
                        rgb = _int_to_rgb_tuple(color_int)
                        font_color = _rgb_tuple_to_hex(rgb)
                        
                        bbox_raw = span.get("bbox", [0.0, 0.0, 0.0, 0.0])
                        bbox = [round(float(c), 2) for c in bbox_raw]

                        # Detect offscreen or clipped positioning
                        is_offscreen = (
                            bbox[0] < -5.0 or 
                            bbox[1] < -5.0 or 
                            bbox[2] > (page_width + 5.0) or 
                            bbox[3] > (page_height + 5.0) or
                            bbox[2] <= bbox[0] or
                            bbox[3] <= bbox[1]
                        )

                        # Detect zero opacity or rendering mode flags if present
                        flags = span.get("flags", 0)
                        is_hidden_flag = bool(flags & 1) or is_offscreen

                        metadata = {
                            "font_name": font_name,
                            "color_int": color_int,
                            "rgb_tuple": rgb,
                            "flags": flags,
                            "page_width": page_width,
                            "page_height": page_height,
                            "is_offscreen": is_offscreen,
                            "source": "NATIVE_PDF"
                        }

                        text_span = TextSpan(
                            text=raw_text,
                            page=page_num + 1,
                            font_size=font_size,
                            font_color=font_color,
                            bg_color="#FFFFFF",  # Default page canvas background
                            bbox=bbox,
                            font_name=font_name,
                            is_hidden=is_hidden_flag,
                            source="NATIVE_PDF",
                            ocr_confidence=None,
                            metadata=metadata
                        )

                        spans.append(text_span)

                        if len(spans) >= self.config.max_spans_per_doc:
                            self.logger.warning(f"Span count limit reached ({self.config.max_spans_per_doc} spans). Halting parsing.")
                            doc.close()
                            return spans

        # Check if native text extraction is insufficient for analysis
        total_native_chars = sum(len(s.text.strip()) for s in spans)
        if total_native_chars < 10:
            self.logger.info(f"Native text extraction insufficient ({total_native_chars} chars extracted). Invoking OCR fallback...")
            try:
                from securoxi.parsers.ocr_engine import OCREngine
                ocr_engine = OCREngine(config=self.config)
                ocr_spans = ocr_engine.perform_ocr(doc, max_pages=total_pages)
                if ocr_spans:
                    self.logger.info(f"OCR fallback succeeded: Appending {len(ocr_spans)} OCR spans.")
                    spans.extend(ocr_spans)
            except Exception as ocr_err:
                self.logger.warning(f"OCR fallback execution warning: {ocr_err}")

        doc.close()
        elapsed_ms = (time.time() - start_time) * 1000
        self.logger.info(f"Parsed {len(spans)} text spans from '{file_path}' across {total_pages} pages in {elapsed_ms:.2f}ms")

        return spans
