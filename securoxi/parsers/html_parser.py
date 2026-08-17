"""
SECUROXI AI HTML Document Parser
Parses HTML documents safely, extracting visible text, detecting hidden CSS styles
(display:none, visibility:hidden, font-size:0, color:transparent), and stripping script tags.
"""

import os
import re
from html.parser import HTMLParser as PythonHTMLParser
from typing import List, Optional, Dict, Any
from securoxi.config import SecuroxiConfig
from securoxi.logger import get_logger
from securoxi.models import TextSpan
from securoxi.parsers.base import BaseParser


class SecuroxiHTMLParser(BaseParser):
    """
    Production-grade HTML parser for SECUROXI AI.
    Extracts text elements while analyzing CSS style attributes for hidden text (display:none, visibility:hidden).
    Does NOT execute scripts or fetch external resources.
    """

    def __init__(self, config: Optional[SecuroxiConfig] = None):
        self.config = config or SecuroxiConfig()
        self.logger = get_logger("securoxi.parsers.html")

    def parse(self, file_path: str) -> List[TextSpan]:
        canonical_path = os.path.abspath(os.path.realpath(file_path))
        if not os.path.isfile(canonical_path):
            raise FileNotFoundError(f"HTML file not found: '{file_path}'")

        file_size = os.path.getsize(canonical_path)
        if file_size > self.config.max_file_size_bytes:
            raise ValueError(f"HTML file size ({file_size} bytes) exceeds maximum limit.")

        try:
            with open(canonical_path, "r", encoding="utf-8", errors="replace") as f:
                html_content = f.read()
        except Exception as err:
            self.logger.error(f"Failed to read HTML file '{file_path}': {err}")
            raise ValueError(f"Failed to read HTML document: {err}")

        spans: List[TextSpan] = []

        class HTMLContentExtractor(PythonHTMLParser):
            def __init__(self):
                super().__init__()
                self.spans: List[TextSpan] = []
                self.current_tag = ""
                self.in_script = False
                self.in_style = False
                self.style_stack = []

            def handle_starttag(self, tag, attrs):
                self.current_tag = tag.lower()
                if self.current_tag in ["script", "noscript"]:
                    self.in_script = True
                elif self.current_tag == "style":
                    self.in_style = True

                attr_dict = dict(attrs)
                style_str = attr_dict.get("style", "").lower()
                is_hidden = bool(
                    "display:none" in style_str.replace(" ", "") or
                    "visibility:hidden" in style_str.replace(" ", "") or
                    "font-size:0" in style_str.replace(" ", "") or
                    "color:transparent" in style_str.replace(" ", "") or
                    "opacity:0" in style_str.replace(" ", "")
                )
                self.style_stack.append(is_hidden)

            def handle_endtag(self, tag):
                tag_lower = tag.lower()
                if tag_lower in ["script", "noscript"]:
                    self.in_script = False
                elif tag_lower == "style":
                    self.in_style = False
                if self.style_stack:
                    self.style_stack.pop()

            def handle_data(self, data):
                if self.in_script or self.in_style:
                    return
                text = data.strip()
                if not text:
                    return

                is_hidden = any(self.style_stack) if self.style_stack else False

                span = TextSpan(
                    text=text,
                    page=1,
                    font_name="Sans-Serif",
                    font_size=12.0,
                    font_color="#000000",
                    bg_color="#FFFFFF",
                    is_hidden=is_hidden,
                    source="NATIVE_HTML",
                    metadata={
                        "source": "NATIVE_HTML",
                        "tag": self.current_tag,
                        "is_hidden_css": is_hidden
                    }
                )
                self.spans.append(span)

        extractor = HTMLContentExtractor()
        extractor.feed(html_content)
        spans = extractor.spans

        return spans
