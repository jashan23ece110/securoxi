# SECUROXI AI Phase 3 — Security Brain Core Architecture Document

**Engine Version**: `0.3.0-brain-core`  
**Classification**: **`ENTERPRISE ARCHITECTURE SPECIFICATION`**  
**Stage 1 Status**: **`PASS`**  
**Date**: `2026-08-14`

---

## 1. Architecture Overview

The **SECUROXI Security Brain** is a 12-component modular security reasoning architecture. It transforms static document threat scanning and candidate resume screening into a unified, continuous enterprise threat reasoning ecosystem.

```
Document / Event / ATS Webhook / Agent Tool Call
                     |
                     v
+-------------------------------------------------------------------+
|               SECUROXI SECURITY BRAIN PIPELINE                    |
|                                                                   |
|  1. Signal Collector      --->  Inbound Signal Normalization       |
|  2. Forensics Engine      --->  Low-level Span & Structural Check  |
|  3. Threat Detector       --->  Pattern & Signature Scanning       |
|  4. Context Enricher      --->  ATS Metadata & Candidate Profile   |
|  5. Correlation Engine    --->  Multi-Signal Incident Synthesis    |
|  6. Attack Graph Builder  --->  Node & Edge Attack Chain Mapping   |
|  7. Security Reasoning    --->  XML-Isolated LLM Context Eval    |
|  8. Risk Engine           --->  Composite Risk Score Propagation   |
|  9. Policy Engine         --->  ALLOW / SUSPEND / QUARANTINE       |
| 10. Action Response Layer --->  Automated Enforcement Triggering   |
| 11. Evidence Store        --->  Signal Provenance Storage          |
| 12. Audit Observability   --->  Structured JSON Metrics & Logs     |
+-------------------------------------------------------------------+
                     |
                     v
       [Policy Decision & Enforcement Action]
```

---

## 2. The 12 Core Components & Data Schemas

1. **`SignalCollector`**: Ingests raw events from documents, ATS webhooks (`EventSource.ATS_INTEGRATION_WEBHOOK`), and AI agent tool calls.
2. **`ForensicsEngine`**: Analyzes font sizes (`< 2.0pt`), RGB white color distance (`#FFFFFF`), vector bounding boxes, and zero-width unicode characters (`unicodedata.category('Cf')`).
3. **`ThreatDetector`**: Identifies prompt injections, system prompt overrides, visual deception, and ATS score manipulation signatures.
4. **`ContextEnricher`**: Enriches signals with candidate profiles, job description constraints, client IP, and ATS user metadata.
5. **`CorrelationEngine`**: Synthesizes multiple related signals across time and sources into a unified `CorrelationObject` incident.
6. **`AttackGraphBuilder`**: Builds a directed graph (`AttackChainGraph`) linking incident nodes, signal nodes, candidate entities, and target ATS systems.
7. **`SecurityReasoningLayer`**: Evaluates threat intent inside an explicit XML prompt isolation boundary (`<untrusted_security_context>`), ensuring untrusted inputs can NEVER execute instruction overrides.
8. **`RiskEngine`**: Computes composite risk scores ($0.0 - 100.0$) using weighted risk propagation.
9. **`PolicyEngine`**: Maps risk scores to explicit enterprise policy actions (`ALLOW`, `WARN_AUDIT`, `SUSPEND_SCREENING`, `QUARANTINE_BLOCK`, `REVOKE_API_ACCESS`).
10. **`ActionResponseLayer`**: Triggers automated enforcement (quarantining high-risk documents, setting candidate fit score to `0.0`, notifying security webhooks).
11. **`EvidenceStore`**: Preserves full signal provenance, raw payloads, and location tracking.
12. **`AuditObservabilityLayer`**: Emits structured JSON audit events and logs for SIEM integration.

---

## 3. Trust Boundaries & Security Directives

* **Deterministic Controls Priority**: Deterministic security controls (parsers, font size calculators, regex injection detectors) remain the primary security authority. The LLM/AI reasoning layer is used strictly for intent classification within XML boundaries.
* **Zero Trust Input Model**: All document text, ATS webhook payloads, and candidate profile strings are treated as untrusted data.
* **Security Always Wins**: Any document triggering `HIGH_RISK` is quarantined prior to candidate screening.

---

## 4. Regression & Unit Test Results (96 Tests)

```text
======================== 96 passed in 0.87s ========================
```
* **Phase 1 Security Engine Tests**: `57 / 57 PASSED`
* **Phase 2 Screening Engine Tests**: `35 / 35 PASSED`
* **Phase 3 Stage 1 Brain Core Tests**: `4 / 4 PASSED`
* **Total Suite**: **`96 / 96 PASSED (100%)`**

---

## 5. Phase 3 Stage 1 Status

# **`PASS`**
