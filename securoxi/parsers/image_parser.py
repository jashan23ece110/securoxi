"""
SECUROXI AI Standalone Image OCR Parser
Parses standalone image files (.png, .jpg, .jpeg, .tiff) using the OCREngine fallback subsystem.
"""

import os
from typing import List, Optional
import fitz  # PyMuPDF

from securoxi.config import SecuroxiConfig
from securoxi.logger import get_logger
from securoxi.models import TextSpan
from securoxi.parsers.base import BaseParser
from securoxi.parsers.ocr_engine import OCREngine


class ImageOCRParser(BaseParser):
    """
    Standalone Image OCR Parser for SECUROXI AI.
    Processes PNG, JPG, JPEG, and TIFF files by embedding image into PyMuPDF container and running OCREngine.
    """

    def __init__(self, config: Optional[SecuroxiConfig] = None):
        self.config = config or SecuroxiConfig()
        self.logger = get_logger("securoxi.parsers.image")
        self.ocr_engine = OCREngine(config=self.config)

    def parse(self, file_path: str) -> List[TextSpan]:
        canonical_path = os.path.abspath(os.path.realpath(file_path))
        if not os.path.isfile(canonical_path):
            raise FileNotFoundError(f"Image file not found: '{file_path}'")

        file_size = os.path.getsize(canonical_path)
        if file_size > self.config.max_file_size_bytes:
            raise ValueError(f"Image file size ({file_size} bytes) exceeds maximum limit.")

        try:
            # Embed image into single-page PyMuPDF Document container for OCR extraction
            doc = fitz.open()
            img_doc = fitz.open(canonical_path)
            rect = img_doc[0].rect
            pdf_bytes = img_doc.convert_to_pdf()
            img_doc.close()

            doc = fitz.open("pdf", pdf_bytes)
            ocr_spans = self.ocr_engine.perform_ocr(doc, max_pages=1)
            doc.close()

            return ocr_spans
        except Exception as err:
            self.logger.error(f"Image OCR parsing failed for '{file_path}': {err}")
            raise ValueError(f"Failed to process image file with OCR: {err}")
