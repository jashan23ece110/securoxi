"""
SECUROXI AI TXT Plain Text Parser
Parses plain text documents with UTF-8 / fallback encoding, Unicode control character detection,
and boundary enforcement.
"""

import os
from typing import List, Optional
from securoxi.config import SecuroxiConfig
from securoxi.logger import get_logger
from securoxi.models import TextSpan
from securoxi.parsers.base import BaseParser


class TXTParser(BaseParser):
    """
    Production-grade TXT parser for SECUROXI AI.
    Extracts text spans, normalizes encoding, and flags invisible Unicode control characters.
    """

    def __init__(self, config: Optional[SecuroxiConfig] = None):
        self.config = config or SecuroxiConfig()
        self.logger = get_logger("securoxi.parsers.txt")

    def parse(self, file_path: str) -> List[TextSpan]:
        canonical_path = os.path.abspath(os.path.realpath(file_path))
        if not os.path.isfile(canonical_path):
            raise FileNotFoundError(f"TXT file not found: '{file_path}'")

        file_size = os.path.getsize(canonical_path)
        if file_size > self.config.max_file_size_bytes:
            raise ValueError(f"TXT file size ({file_size} bytes) exceeds maximum limit.")

        try:
            with open(canonical_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as err:
            self.logger.error(f"Failed to read TXT file '{file_path}': {err}")
            raise ValueError(f"Failed to read TXT document: {err}")

        spans: List[TextSpan] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines):
            raw_text = line.strip()
            if not raw_text:
                continue

            # Detect invisible Unicode control characters (e.g. \u200B zero-width space, \u202A, \uFEFF)
            contains_invisible = any(
                char in raw_text for char in ["\u200B", "\u200C", "\u200D", "\u202A", "\u202B", "\u202C", "\u202D", "\u202E", "\uFEFF"]
            )

            span = TextSpan(
                text=raw_text,
                page=1,
                font_name="Monospace",
                font_size=11.0,
                font_color="#000000",
                bg_color="#FFFFFF",
                is_hidden=contains_invisible,
                source="NATIVE_TXT",
                metadata={
                    "source": "NATIVE_TXT",
                    "line_number": idx + 1,
                    "contains_invisible_unicode": contains_invisible
                }
            )
            spans.append(span)

            if len(spans) >= self.config.max_spans_per_doc:
                self.logger.warning(f"Span limit reached ({self.config.max_spans_per_doc}) in TXT parser.")
                break

        return spans
