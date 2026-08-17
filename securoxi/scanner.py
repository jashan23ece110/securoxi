"""
SECUROXI AI Top-Level Scanner Service
Orchestrates the end-to-end security pipeline:
Input Validation -> Parser Selection -> Text Extraction & Normalization 
-> Visual Deception Analysis -> Prompt Injection Analysis 
-> Risk Correlation & Scoring -> Security Report Generation
"""

import os
import time
from typing import Optional, Dict, Any
from securoxi.config import SecuroxiConfig
from securoxi.logger import get_logger
from securoxi.models import AnalysisReport, Verdict
from securoxi.engine import SecuroxiEngine


class SecuroxiScanner:
    """
    Top-level scanner orchestrator for SECUROXI AI.
    Provides a clean, unified API for scanning documents and receiving structured security reports.
    """

    def __init__(self, config: Optional[SecuroxiConfig] = None):
        self.config = config or SecuroxiConfig()
        self.logger = get_logger("securoxi.scanner")
        self.engine = SecuroxiEngine(config=self.config)

    def scan(self, file_path: str) -> AnalysisReport:
        """
        Execute end-to-end document security scan.
        Returns a structured AnalysisReport.
        """
        self.logger.info(f"Initiating end-to-end security scan for document: '{file_path}'")
        
        # Delegate parsing, normalization, analysis, and risk scoring to engine
        report = self.engine.analyze_document(file_path)

        # Enrich report metadata with scanner version and timestamp
        report.metadata["scanner"] = "SECUROXI AI Scanner v0.1.0"
        report.metadata["scanned_at"] = time.strftime('%Y-%m-%d %H:%M:%S')

        return report

    def scan_to_dict(self, file_path: str) -> Dict[str, Any]:
        """Execute scan and return result as JSON-serializable dictionary."""
        report = self.scan(file_path)
        return report.to_dict()
