# SECUROXI AI Phase 3 — ATS Integration Framework Architecture Specification

**Engine Version**: `0.3.0-ats-framework`  
**Classification**: **`ENTERPRISE ATS INTEGRATION ARCHITECTURE SPECIFICATION`**  
**Stage 5 Status**: **`PASS`**  
**Date**: `2026-08-14`

---

## 1. Architecture Overview & Ingestion Flow

The **SECUROXI ATS Integration Framework** connects enterprise Applicant Tracking Systems (Greenhouse, Lever, Workday, or custom providers) via a provider-agnostic adapter layer (`BaseATSAdapter`).

```
                    [Enterprise ATS Webhook Payload]
                                   |
                                   v
+-------------------------------------------------------------------+
|               SECUROXI ATS ADAPTER LAYER                          |
|                                                                   |
|  1. HMAC Signature Verification ---> Verify SHA-256 Secret Header |
|  2. Idempotency Check           ---> Deduplicate Event IDs        |
|  3. Payload Normalization       ---> Parse to ATSWebhookEvent     |
+-------------------------------------------------------------------+
                                   |
                                   v
+-------------------------------------------------------------------+
|               MANDATORY SECURITY GATE SCAN                        |
|               (Untrusted document NEVER bypasses Phase 1)         |
|                                                                   |
|  Phase 1 Security Scan Gate  ---> Visual Deception & Injection    |
|  Phase 2 Screening Engine    ---> Match Score & Candidate Report  |
+-------------------------------------------------------------------+
                                   |
                                   v
       [ATS Screening Status Sync: SAFE / SUSPICIOUS / HIGH_RISK]
```

---

## 2. Base ATS Adapter & Provider Abstraction

```
                      BaseATSAdapter (Abstract Base)
                                    |
        +---------------------------+---------------------------+
        |                           |                           |
  MockATSAdapter            GreenhouseAdapter            WorkdayAdapter
  (Mock Enterprise Provider) (Provider Interface)        (Provider Interface)
```

* **`verify_webhook_signature(raw_body, signature_header)`**: Enforces HMAC-SHA256 signature verification prior to payload parsing.
* **`is_duplicate_event(event_id)`**: Idempotency check preventing duplicate processing of retried webhook events.
* **`sync_screening_result(candidate_id, report)`**: Pushes SECUROXI security verdict and fit score back to the target ATS.
* **`execute_with_retry(func, max_retries, delay_sec)`**: Retries failed ATS requests using exponential backoff.

---

## 3. Security Controls & Guarantees

1. **Mandatory Phase 1 Security Gate**: All incoming ATS document attachments must pass Phase 1 security scanning first. Documents triggering `HIGH_RISK` are **quarantined** with score `0.0`.
2. **HMAC Signature Verification**: Webhooks without a valid HMAC signature are rejected immediately with `success = False`.
3. **Idempotency Protection**: In-memory event ID tracking prevents duplicate screening executions.
4. **Secret Isolation**: Secrets (`webhook_secret`, `api_key`) are isolated in `ATSAuthenticationConfig` objects and excluded from system log traces.

---

## 4. Empirical Test Results (115 Tests)

```text
======================= 115 passed in 1.02s ========================
```
* **Phase 1 Security Engine Tests**: `57 / 57 PASSED`
* **Phase 2 Screening Engine Tests**: `35 / 35 PASSED`
* **Phase 3 Stage 1 Brain Core Tests**: `4 / 4 PASSED`
* **Phase 3 Stage 2 Threat Intel Tests**: `3 / 3 PASSED`
* **Phase 3 Stage 3 Runtime Security Tests**: `6 / 6 PASSED`
* **Phase 3 Stage 4 Policy Engine Tests**: `5 / 5 PASSED`
* **Phase 3 Stage 5 ATS Integration Tests**: `5 / 5 PASSED`
* **Total Suite**: **`115 / 115 PASSED (100%)`**

---

## 5. Known Limitations

1. **Mock Provider Default**: Production API keys for live Greenhouse/Lever environments require enterprise customer provisioning. The `MockATSAdapter` fully simulates live ATS behavior for testing and staging deployment.

---

## 6. Phase 3 Stage 5 Status

# **`PASS`**
