"""
SECUROXI AI Phase 3 Stage 5 — Mock Enterprise ATS Provider Adapter
Implements HMAC-SHA256 signature verification, idempotency deduplication, retry handling,
and security-aware screening pipeline integration.
"""

import hmac
import hashlib
import time
from typing import Dict, Any, Optional, Callable
from securoxi.integrations.ats_base import (
    BaseATSAdapter, ATSWebhookEvent, ATSAuthenticationConfig, ATSActionResult
)
from securoxi.screening.pipeline import SecuroxiScreeningPipeline
from securoxi.config import SecuroxiConfig
from securoxi.logger import get_logger


class MockATSAdapter(BaseATSAdapter):
    """
    Mock Enterprise ATS Provider Adapter.
    Enforces HMAC verification, event deduplication, retry handler, and security gate pipeline integration.
    """

    def __init__(self, config: Optional[ATSAuthenticationConfig] = None):
        cfg = config or ATSAuthenticationConfig(
            provider_name="MOCK_ENTERPRISE_ATS",
            api_key="mock_key_securoxi_12345",
            webhook_secret="securoxi_webhook_secret_9999"
        )
        super().__init__(cfg)
        self.logger = get_logger("securoxi.integrations.mock_ats")
        self.pipeline = SecuroxiScreeningPipeline(config=SecuroxiConfig())
        self.synced_results: Dict[str, Dict[str, Any]] = {}

    def verify_webhook_signature(self, raw_body: bytes, signature_header: str) -> bool:
        """Verifies HMAC-SHA256 signature header against webhook secret."""
        if not signature_header:
            return False
        expected_sig = hmac.new(
            self.config.webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_sig, signature_header)

    def parse_webhook_event(self, payload: Dict[str, Any]) -> ATSWebhookEvent:
        """Parses webhook payload into normalized ATSWebhookEvent."""
        event_id = payload.get("event_id", f"EVT-{int(time.time())}")
        return ATSWebhookEvent(
            event_id=event_id,
            event_type=payload.get("event_type", "RESUME_ATTACHED"),
            provider_name=self.config.provider_name,
            candidate_id=payload.get("candidate_id", "CANDIDATE_001"),
            job_id=payload.get("job_id", "JOB_001"),
            file_path=payload.get("file_path"),
            raw_payload=payload
        )

    def process_incoming_webhook(
        self, raw_body: bytes, signature_header: str, payload: Dict[str, Any], jd_source: Any
    ) -> ATSActionResult:
        """
        End-to-End Security-Aware ATS Webhook Processing:
        1. HMAC Signature Verification.
        2. Idempotency Event Deduplication.
        3. Mandatory Phase 1 Security Gate Scan & Phase 2 Screening.
        4. Status Sync back to ATS.
        """
        # Step 1: Verify HMAC Signature
        if not self.verify_webhook_signature(raw_body, signature_header):
            self.logger.warning("ATS Webhook Signature Verification FAILED!")
            return ATSActionResult(success=False, operation="WEBHOOK_VERIFICATION", message="Invalid HMAC signature header.")

        # Step 2: Idempotency Check
        evt = self.parse_webhook_event(payload)
        if self.is_duplicate_event(evt.event_id):
            self.logger.info(f"Duplicate ATS Webhook event detected: '{evt.event_id}'. Ignoring.")
            return ATSActionResult(success=True, operation="DEDUPLICATION", message=f"Duplicate event '{evt.event_id}' skipped.", event_id=evt.event_id)

        # Step 3: Mandatory Phase 1 Security Gate & Screening Pipeline Execution
        if not evt.file_path:
            return ATSActionResult(success=False, operation="INGESTION", message="Missing resume file path in payload.", event_id=evt.event_id)

        screening_res = self.pipeline.screen_resume(evt.file_path, jd_source)

        # Step 4: Sync Result Back to ATS
        sync_res = self.sync_screening_result(evt.candidate_id, screening_res)

        return ATSActionResult(
            success=True,
            operation="PROCESS_WEBHOOK",
            message=f"Webhook '{evt.event_id}' processed cleanly. Security Verdict: {screening_res['security_verdict']}",
            event_id=evt.event_id,
            data={"screening_result": screening_res, "sync_status": sync_res.message}
        )

    def sync_screening_result(self, candidate_id: str, screening_report: Dict[str, Any]) -> ATSActionResult:
        """Stores screening verdict in ATS candidate records."""
        self.synced_results[candidate_id] = screening_report
        self.logger.info(f"Screening result for candidate '{candidate_id}' synced cleanly to ATS.")
        return ATSActionResult(
            success=True,
            operation="SYNC_RESULT",
            message=f"Screening verdict '{screening_report.get('security_verdict')}' synced for candidate '{candidate_id}'."
        )

    def execute_with_retry(self, func: Callable[[], Any], max_retries: int = 3, delay_sec: float = 0.1) -> Any:
        """Executes operation with exponential backoff retry handler."""
        for attempt in range(1, max_retries + 1):
            try:
                return func()
            except Exception as err:
                self.logger.warning(f"Attempt {attempt}/{max_retries} failed: {err}")
                if attempt == max_retries:
                    raise err
                time.sleep(delay_sec * (2 ** (attempt - 1)))
