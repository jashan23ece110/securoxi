"""
SECUROXI AI Phase 2 Stage 8 — Security-Aware Screening Pipeline
Enforces Phase 1 Security Scanning as a mandatory gate before Resume-to-JD screening.
Quarantines malicious high-risk resumes and flags suspicious formatting for human review.
"""

from typing import List, Dict, Any, Optional
from securoxi.config import SecuroxiConfig
from securoxi.logger import get_logger
from securoxi.scanner import SecuroxiScanner
from securoxi.models import AnalysisReport, Verdict
from securoxi.screening.ingestion import SecuroxiIngestionEngine
from securoxi.screening.extractor import RuleBasedExtractor
from securoxi.screening.matching_engine import SecuroxiMatchingEngine
from securoxi.screening.qualification_analyzer import SecuroxiQualificationAnalyzer
from securoxi.screening.scorer import SecuroxiCandidateScorer
from securoxi.screening.report_generator import SecuroxiReportGenerator
from securoxi.screening.report_models import ScreeningReport, RecommendationCategory, RequirementEvidenceLink


class SecuroxiScreeningPipeline:
    """
    End-to-End Security-Aware Screening Pipeline.
    Ensures security gate evaluates untrusted resumes first.
    HIGH_RISK documents are blocked from automated screening.
    """

    def __init__(self, config: Optional[SecuroxiConfig] = None):
        self.config = config or SecuroxiConfig()
        self.logger = get_logger("securoxi.screening.pipeline")
        self.scanner = SecuroxiScanner(config=self.config)
        self.ingestion_engine = SecuroxiIngestionEngine(config=self.config)
        self.extractor = RuleBasedExtractor()
        self.matching_engine = SecuroxiMatchingEngine()
        self.qualification_analyzer = SecuroxiQualificationAnalyzer()
        self.scorer = SecuroxiCandidateScorer()
        self.report_generator = SecuroxiReportGenerator()

    def screen_resume(
        self,
        resume_path: str,
        jd_source: Any,
        block_high_risk: bool = True
    ) -> Dict[str, Any]:
        """
        Execute Security-Aware Screening Pipeline:
        1. Phase 1 Security Gate Scan.
        2. Policy evaluation (SAFE / SUSPICIOUS / HIGH_RISK).
        3. Resume-to-JD Analysis (if security gate passes).
        """
        self.logger.info(f"Initiating Security-Aware Screening for: '{resume_path}'")

        # Step 1: Mandatory Phase 1 Security Scan Gate
        security_report: AnalysisReport = self.scanner.scan(resume_path)

        # Step 2: Policy Enforcement (HIGH_RISK & UNINSPECTABLE documents MUST NOT silently proceed!)
        analysis_status_val = getattr(security_report, "analysis_status", "ANALYZED")
        if hasattr(analysis_status_val, "value"):
            analysis_status_val = analysis_status_val.value

        if (security_report.verdict in [Verdict.HIGH_RISK, Verdict.SUSPICIOUS] or analysis_status_val == "UNINSPECTABLE") and block_high_risk:
            self.logger.warning(f"SECURITY GATE TRIGGERED: High risk or uninspectable resume '{resume_path}' (Verdict={security_report.verdict.value}, Status={analysis_status_val}) blocked from automated screening!")
            return self._build_quarantine_report(resume_path, security_report)

        # Step 3: Execute Ingestion & Structuring Pipeline
        resume_doc = self.ingestion_engine.ingest_resume(resume_path)
        jd_doc = self.ingestion_engine.ingest_job_description(jd_source)

        resume_prof = self.extractor.extract_resume_profile(resume_doc)
        jd_prof = self.extractor.extract_jd_profile(jd_doc)

        match_rep = self.matching_engine.match_resume_to_jd(resume_prof, jd_prof)
        qual_rep = self.qualification_analyzer.analyze_qualifications(resume_prof, jd_prof)
        score_rep = self.scorer.score_candidate(resume_prof, jd_prof, match_rep, qual_rep)

        screening_report = self.report_generator.generate_report(
            resume_prof, jd_prof, match_rep, qual_rep, score_rep
        )

        report_dict = screening_report.to_dict()
        report_dict["security_report"] = security_report.to_dict()
        report_dict["requires_human_security_review"] = (security_report.verdict != Verdict.SAFE)

        return {
            "security_verdict": security_report.verdict.value,
            "security_risk_score": security_report.risk_score,
            "screening_report": report_dict,
            "markdown_report": screening_report.to_markdown()
        }

    def rank_resumes(
        self,
        resume_paths: List[str],
        jd_source: Any,
        block_high_risk: bool = True
    ) -> Dict[str, Any]:
        """
        Execute Security-Aware Multi-Candidate Ranking.
        Quarantines malicious resumes at the bottom of ranking with score 0.0.
        """
        self.logger.info(f"Initiating Security-Aware Ranking across {len(resume_paths)} resumes.")

        results: List[Dict[str, Any]] = []

        for path in resume_paths:
            try:
                res = self.screen_resume(path, jd_source, block_high_risk=block_high_risk)
                results.append(res)
            except Exception as err:
                self.logger.error(f"Error screening resume '{path}': {err}")

        # Sort results by fit_score descending (Quarantined high-risk resumes have fit_score 0.0)
        results.sort(
            key=lambda x: x["screening_report"].get("match_score", 0.0),
            reverse=True
        )

        return {
            "total_resumes_processed": len(results),
            "safe_count": sum(1 for r in results if r["security_verdict"] == "SAFE"),
            "suspicious_count": sum(1 for r in results if r["security_verdict"] == "SUSPICIOUS"),
            "high_risk_quarantined_count": sum(1 for r in results if r["security_verdict"] == "HIGH_RISK"),
            "ranked_results": results
        }

    def _build_quarantine_report(
        self, resume_path: str, security_report: AnalysisReport
    ) -> Dict[str, Any]:
        """Builds a quarantined screening response for high-risk malicious resumes."""
        import os
        filename = os.path.basename(resume_path)

        rep_id = getattr(security_report, "scan_id", getattr(security_report, "report_id", security_report.filename))

        quarantine_report = {
            "report_id": f"REP-QUARANTINE-{rep_id}",
            "candidate_id": "QUARANTINED_FILE",
            "candidate_name": f"QUARANTINED: {filename}",
            "jd_id": "BLOCKED",
            "job_title": "BLOCKED_DUE_TO_SECURITY_THREAT",
            "match_score": 0.0,
            "recommendation": "INSUFFICIENT_DATA",
            "required_matches": [],
            "required_missing": [],
            "preferred_matches": [],
            "experience_summary": "Automated screening blocked due to high-risk security threats.",
            "education_summary": "BLOCKED",
            "strengths": [],
            "gaps": ["Document quarantined due to active prompt injection / visual deception attack"],
            "uncertainties": ["Untrusted document contents quarantined"],
            "security_verdict": security_report.verdict.value,
            "human_review_disclaimer": "SECURITY ALERT: This document triggered security analyzer detection flags and was blocked from automated candidate screening.",
            "security_report": security_report.to_dict(),
            "requires_human_security_review": True
        }

        md_quarantine = (
            f"# ⚠️ SECUROXI SECURITY ALERT: DOCUMENT QUARANTINED\n"
            f"**File**: `{filename}` | **Report ID**: `{rep_id}`\n"
            f"**Security Verdict**: **`HIGH_RISK`** (Risk Score: {security_report.risk_score}/100)\n"
            f"**Primary Threat Signal**: `{security_report.primary_threat}`\n\n"
            f"> **Automated Screening Status**: **BLOCKED**\n"
            f"> This document contains active visual deception, hidden text, or prompt injection attacks "
            f"and was quarantined to protect the screening pipeline."
        )



        return {
            "security_verdict": security_report.verdict.value,
            "security_risk_score": security_report.risk_score,
            "screening_report": quarantine_report,
            "markdown_report": md_quarantine
        }
