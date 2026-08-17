# SECUROXI AI Phase 3 — Threat Intelligence & Attack Graph Model Specification

**Engine Version**: `0.3.0-threat-intel`  
**Classification**: **`ENTERPRISE SECURITY THREAT INTEL SPECIFICATION`**  
**Stage 2 Status**: **`PASS`**  
**Date**: `2026-08-14`

---

## 1. Threat Graph Model Overview

The **SECUROXI Threat Intelligence & Attack Graph Model** represents security findings not as isolated text alerts, but as structured, contextualized attack chain relationships.

```
+-----------------------------------------------------------------------------------+
|                        SECUROXI THREAT RELATIONSHIP GRAPH                         |
|                                                                                   |
|  [Actor / Source Artifact] ---> (Resume PDF / Webhook Payload)                    |
|            |                                                                      |
|            v                                                                      |
|     [Security Signal]      ---> (MICRO_WHITE_TEXT / INSTRUCTION_OVERRIDE)         |
|            |                                                                      |
|            v                                                                      |
|   [Attack Technique]       ---> (T-1001: White Text / T-1003: Prompt Injection)   |
|            |                                                                      |
|            v                                                                      |
|    [Target System]         ---> (RESUME_SCREENING_PIPELINE / ATS_WEBHOOK)         |
|            |                                                                      |
|            v                                                                      |
|   [Potential Impact]       ---> (RANKING_MANIPULATION / AI_HIJACKING)             |
|            |                                                                      |
|            v                                                                      |
|    [Policy Action]         ---> (QUARANTINE_BLOCK / SUSPEND_SCREENING)            |
+-----------------------------------------------------------------------------------+
```

---

## 2. Threat Categories & Technique Catalog

SECUROXI defines 8 specialized threat categories and standard attack technique identifiers:

1. **`PROMPT_INJECTION`**: Direct or indirect commands attempting to override LLM system prompts (`T-1003`).
2. **`INSTRUCTION_HIJACKING`**: Diverting AI reasoning from screening candidates to unauthorized tasks.
3. **`RANKING_MANIPULATION`**: Commands forcing ATS screening algorithms to grant score 100/100 or `STRONG_MATCH` (`T-1004`).
4. **`DATA_EXFILTRATION`**: Formatting text or markdown images to exfiltrate system context to external URLs.
5. **`TOOL_MANIPULATION`**: Crafted instructions attempting to invoke system CLI tools or external API actions.
6. **`OBFUSCATION`**: Encoding payloads using base64, homoglyphs, or invisible unicode characters (`unicodedata.category('Cf')`).
7. **`HIDDEN_CONTENT`**: Micro-text font size `< 2.0pt` (`T-1002`) or white font color `#FFFFFF` (`T-1001`).
8. **`AGENT_MANIPULATION`**: Subverting multi-agent orchestration states or session memory.

---

## 3. Multi-Signal & Recurrence Tracking

* **Signal Correlation**: Multiple signals (e.g. font size 0.5pt + text "Ignore previous instructions") are grouped into a single `CorrelationObject` incident.
* **Recurrence Tracking**: `ThreatIntelRecord` maintains `recurrence_count`, `first_seen`, and `last_seen` timestamps to identify repeated attack vectors originating from the same source or IP.
* **Provenance Integrity**: Every node in the Threat Graph retains `evidence_provenance` linking back to the exact document line or section location.

---

## 4. Empirical Test Results (99 Tests)

```text
======================== 99 passed in 1.04s ========================
```
* **Phase 1 Security Engine Tests**: `57 / 57 PASSED`
* **Phase 2 Screening Engine Tests**: `35 / 35 PASSED`
* **Phase 3 Stage 1 Brain Core Tests**: `4 / 4 PASSED`
* **Phase 3 Stage 2 Threat Intel Tests**: `3 / 3 PASSED`
* **Total Suite**: **`99 / 99 PASSED (100%)`**

---

## 5. Known Limitations

1. **Static External Feeds**: External STIX/TAXII threat intel feeds are supported via adapter interfaces but are not active by default to maintain zero-network isolation.

---

## 6. Phase 3 Stage 2 Status

# **`PASS`**
