"""
SECUROXI AI Production Observability & SIEM Integration Test Suite
Validates vendor-neutral SIEM schema serialization (JSON & CEF), export adapter resilience,
fail-safe isolation during monitoring outages, and telemetry metrics reporting.
"""

import pytest
from securoxi.monitoring.siem import NormalizedSecurityEvent, SecuroxiSIEMExporter


def test_normalized_security_event_json_serialization():
    """Verify NormalizedSecurityEvent serializes cleanly to JSON with trace_id and tenant_id."""
    evt = NormalizedSecurityEvent(
        event_type="PROMPT_INJECTION_DETECTED",
        severity="HIGH",
        tenant_id="TENANT-ALPHA",
        attack_category="SYSTEM_PROMPT_MANIPULATION",
        affected_asset="candidate_resume_99.pdf",
        policy_decision="QUARANTINE_DOCUMENT",
        action="BLOCKED",
        trace_id="TRACE-SEC-001"
    )

    json_str = evt.to_json()
    assert "PROMPT_INJECTION_DETECTED" in json_str
    assert "TENANT-ALPHA" in json_str
    assert "TRACE-SEC-001" in json_str
    assert "QUARANTINE_DOCUMENT" in json_str


def test_normalized_security_event_cef_serialization():
    """Verify Common Event Format (CEF) string generation."""
    evt = NormalizedSecurityEvent(
        event_type="VISUAL_DECEPTION",
        severity="MEDIUM",
        tenant_id="TENANT-DEFAULT",
        attack_category="MICRO_TEXT"
    )

    cef_str = evt.to_cef()
    assert cef_str.startswith("CEF:0|SECUROXI|SecurityEngine|0.5.0|VISUAL_DECEPTION|MICRO_TEXT|MEDIUM|")


def test_siem_exporter_dryrun_mode():
    """Verify SecuroxiSIEMExporter handles dry-run logging export without errors."""
    exporter = SecuroxiSIEMExporter(endpoint_url=None, vendor="generic_webhook")
    evt = NormalizedSecurityEvent(event_type="TEST_SCAN", severity="INFO")
    
    success = exporter.export_event(evt)
    assert success is True
    
    stats = exporter.get_telemetry_stats()
    assert stats["exported_events"] == 1
    assert stats["failed_exports"] == 0


def test_siem_exporter_failsafe_isolation():
    """Verify SIEM export failure (unreachable endpoint) never throws or crashes application."""
    # Point to invalid unreachable endpoint URL
    exporter = SecuroxiSIEMExporter(endpoint_url="http://127.0.0.1:9999/invalid_siem_endpoint", vendor="splunk")
    evt = NormalizedSecurityEvent(event_type="FAILSAFE_TEST", severity="HIGH")

    # Call export_event: must return False safely without raising an exception!
    success = exporter.export_event(evt)
    assert success is False

    stats = exporter.get_telemetry_stats()
    assert stats["failed_exports"] == 1
    assert stats["status"] == "OPERATIONAL"
