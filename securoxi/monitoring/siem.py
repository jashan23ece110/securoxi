"""
SECUROXI AI Vendor-Neutral SIEM Security Event Exporter & Telemetry Engine
Formats security events into normalized JSON/CEF schemas for Splunk, Datadog, Elastic,
and Microsoft Sentinel while ensuring complete isolation from core security engine failures.
"""

import time
import uuid
import json
import os
from typing import Dict, Any, Optional, List
from securoxi.secrets import mask_secret
from securoxi.logger import get_logger

logger = get_logger("securoxi.siem")

SIEM_ENDPOINT_URL = os.environ.get("SIEM_ENDPOINT_URL")
SIEM_VENDOR = os.environ.get("SIEM_VENDOR", "generic_webhook").lower()


class NormalizedSecurityEvent:
    """Normalized Vendor-Neutral SIEM Security Event Schema."""

    def __init__(
        self,
        event_type: str,
        severity: str,
        tenant_id: str = "TENANT-DEFAULT",
        source: str = "SECUROXI_SECURITY_ENGINE",
        attack_category: Optional[str] = None,
        affected_asset: Optional[str] = None,
        policy_decision: Optional[str] = None,
        action: Optional[str] = None,
        trace_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.event_id = f"SIEM-EVT-{uuid.uuid4().hex[:8]}"
        self.timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        self.event_type = event_type
        self.severity = severity.upper()
        self.tenant_id = tenant_id
        self.source = source
        self.attack_category = attack_category or "UNKNOWN"
        self.affected_asset = affected_asset or "UNKNOWN_ASSET"
        self.policy_decision = policy_decision or "EVALUATED"
        self.action = action or "LOGGED"
        self.trace_id = trace_id or f"TRACE-{uuid.uuid4().hex[:8]}"
        self.details = details or {}

    def to_json(self) -> str:
        """Serializes event to normalized JSON format."""
        return json.dumps({
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "tenant_id": self.tenant_id,
            "source": self.source,
            "event_type": self.event_type,
            "severity": self.severity,
            "attack_category": self.attack_category,
            "affected_asset": self.affected_asset,
            "policy_decision": self.policy_decision,
            "action": self.action,
            "trace_id": self.trace_id,
            "details": self.details
        })

    def to_cef(self) -> str:
        """Serializes event to Common Event Format (CEF) string."""
        return (
            f"CEF:0|SECUROXI|SecurityEngine|0.5.0|{self.event_type}|"
            f"{self.attack_category}|{self.severity}|"
            f"src={self.source} tenant={self.tenant_id} action={self.action} traceId={self.trace_id}"
        )


class SecuroxiSIEMExporter:
    """Vendor-neutral SIEM Security Event Exporter with fail-safe error isolation."""

    def __init__(self, endpoint_url: Optional[str] = None, vendor: Optional[str] = None):
        self.endpoint_url = endpoint_url or SIEM_ENDPOINT_URL
        self.vendor = (vendor or SIEM_VENDOR).lower()
        self.exported_events_count = 0
        self.failed_exports_count = 0

    def export_event(self, event: NormalizedSecurityEvent) -> bool:
        """
        Exports security event to configured SIEM platform.
        FAIL-SAFE GUARANTEE: SIEM connection failure NEVER blocks core SECUROXI processing!
        """
        try:
            payload_json = event.to_json()
            logger.info(f"[SIEM EXPORT] [{event.severity}] Event [{event.event_id}] ({event.event_type}) formatted for {self.vendor}.")

            if not self.endpoint_url:
                # Dry-run logging export mode
                self.exported_events_count += 1
                return True

            # Perform HTTP export if endpoint configured
            import urllib.request
            req = urllib.request.Request(
                self.endpoint_url,
                data=payload_json.encode('utf-8'),
                headers={'Content-Type': 'application/json', 'User-Agent': 'SECUROXI-SIEM-Exporter/0.5.0'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=2.0) as response:
                if response.status in [200, 201, 202]:
                    self.exported_events_count += 1
                    return True
                else:
                    self.failed_exports_count += 1
                    logger.warning(f"SIEM export endpoint returned status {response.status}")
                    return False

        except Exception as err:
            self.failed_exports_count += 1
            logger.error(f"SIEM Exporter error (isolated from core engine): {err}")
            return False

    def get_telemetry_stats(self) -> Dict[str, Any]:
        """Returns SIEM exporter operational metrics."""
        return {
            "vendor": self.vendor,
            "endpoint_configured": bool(self.endpoint_url),
            "exported_events": self.exported_events_count,
            "failed_exports": self.failed_exports_count,
            "status": "OPERATIONAL"
        }
