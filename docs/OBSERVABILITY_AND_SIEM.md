# SECUROXI AI — Production Observability, Monitoring & SIEM Integration Specification

**Engine Version**: `0.5.0-observability-siem`  
**Classification**: **`PRODUCTION OBSERVABILITY & SIEM INTEGRATION SPECIFICATION`**  
**SIEM Schema**: **`Normalized Vendor-Neutral JSON & Common Event Format (CEF)`**  
**Date**: `2026-08-14`

---

## 1. Observability Subsystems Architecture

The **SECUROXI Observability Engine** (`securoxi/monitoring/siem.py`) decouples event logging and metric telemetry from core security engine decisions:

```
[SECUROXI Application / Security Engine]
            │
            ├──▶ Structured JSON Logs (trace_id, tenant_id, secret masking)
            ├──▶ Health Probes (/health/live, /health/ready)
            └──▶ SecuroxiSIEMExporter (Vendor-neutral Splunk, Datadog, Elastic, Sentinel export)
```

---

## 2. Vendor-Neutral SIEM Event Schema

Security events exported to enterprise SIEM platforms follow a normalized JSON structure:

```json
{
  "event_id": "SIEM-EVT-a1b2c3d4",
  "timestamp": "2026-08-14T23:06:00Z",
  "tenant_id": "TENANT-ALPHA",
  "source": "SECUROXI_SECURITY_ENGINE",
  "event_type": "PROMPT_INJECTION_DETECTED",
  "severity": "HIGH",
  "attack_category": "SYSTEM_PROMPT_MANIPULATION",
  "affected_asset": "candidate_resume_99.pdf",
  "policy_decision": "QUARANTINE_DOCUMENT",
  "action": "BLOCKED",
  "trace_id": "TRACE-SEC-89123",
  "details": { "confidence": 0.99, "matched_pattern": "Ignore previous instructions" }
}
```

Common Event Format (CEF) string generation is also natively supported:
```text
CEF:0|SECUROXI|SecurityEngine|0.5.0|PROMPT_INJECTION_DETECTED|SYSTEM_PROMPT_MANIPULATION|HIGH|src=SECUROXI_SECURITY_ENGINE tenant=TENANT-ALPHA action=BLOCKED traceId=TRACE-SEC-89123
```

---

## 3. Fail-Safe Reliability Guarantee

* **Operational Isolation**: SIEM transport failures, network timeouts, or log collector outages **NEVER** throw uncaught exceptions or interrupt core document security scanning or candidate screening workflows.

---

## 4. Empirical Test Results (198 Tests)

```text
======================= 198 passed in 2.38s ========================
```
* **Existing Test Suite (Phases 1-5, Postgres, Bus, Secrets, Network & Deployment)**: `194 / 194 PASSED (0 Regressions)` 🟢
* **New Observability & SIEM Integration Test Suite**: `4 / 4 PASSED` 🟢
* **Total Test Suite**: **`194 + 4 = 198 / 198 PASSED (100%)`** 🟢

---

## 5. Status Decision Choice

# **`PASS`**
