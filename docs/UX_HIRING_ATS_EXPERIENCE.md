# SECUROXI AI — Hiring Security & ATS Integration Experience

**Module**: Secure Hiring & ATS Connectors  
**Components**: [`ScreeningPage.tsx`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/Screening.tsx), [`ATSPage.tsx`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/ATS.tsx)  
**Backend Endpoints**: `GET /api/v1/screenings`, `POST /api/v1/screening/pipeline/screen`, `POST /api/v1/screening/pipeline/rank`  
**Routes**: `/ats`, `/screening`  
**Test Baseline**: `246 / 246 PASSED` (in 3.36s)  
**Frontend Compilation**: `tsc && vite build` $\rightarrow$ `✓ built in 1.25s`  
**Status**: Verified & Operational  

---

## 1. Executive Summary

The **Hiring Security + ATS Experience** protects hiring pipelines and candidate screening against adversarial document tampering before documents reach downstream recruiters or language models:

> **Connect ATS** $\longrightarrow$ **Select Job Requisition** $\longrightarrow$ **Automatic Security Scan** $\longrightarrow$ **Security Clearance Gate** $\longrightarrow$ **Screening & Calibrated Fit Score** $\longrightarrow$ **Recruiter Decision**

---

## 2. Automatic Security-First Screening Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ATS INBOUND PIPELINE (Greenhouse / Lever / Workday Webhook Sync)                                │
└────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ SECURITY GATE SCAN (Phase 1 Deep Layout & Anomaly Engine)                                       │
│                                                                                                 │
│  • Prompt Injection Detection                                                                   │
│  • Layout Deception / Micro Text (Font < 4.0pt)                                                  │
│  • Background Color Matching / White-on-White Text                                              │
│  • OCR Sandbox Evaluation for Scanned Images                                                    │
└────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                 │
                        ┌────────────────────────┴────────────────────────┐
                        │                                                 │
               [ SAFE / CLEARED ]                              [ HIGH RISK / BLOCKED ]
                        │                                                 │
                        ▼                                                 ▼
┌───────────────────────────────────────────────┐ ┌───────────────────────────────────────────────┐
│ STRUCTURED SCREENING ENGINE                   │ │ SECURITY QUARANTINE GATED                     │
│                                               │ │                                               │
│  • Resume Text Normalization                  │ │  • Rank: Frozen at #0                         │
│  • Required & Preferred Skills Matrix         │ │  • Fit Score: 0.0 / 100                       │
│  • Semantic Match vs Job Target               │ │  • Status: QUARANTINED                        │
│  • Calibrated Fit Score (0–100)               │ │  • Action: Inspect Forensic Evidence          │
└───────────────────────────────────────────────┘ └───────────────────────────────────────────────┘
```

---

## 3. Strict Invariant: Security Clearance vs Fit Score Separation

* **Security Clearance** determines whether the document is trusted for downstream automated evaluation.
* **Fit Score** measures how closely the candidate's skills and experience match the Job Description.

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ CANDIDATE: Sarah Miller                                                                         │
│ Security Clearance: [ SAFE ]                Fit Score: 94.2 / 100 [ STRONG MATCH ]              │
│ Status: QUALIFIED (Cleared for Technical Interview)                                             │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ CANDIDATE: Adversarial Payload Resume                                                           │
│ Security Clearance: [ HIGH RISK ] (Blocked) Fit Score: 0.0 / 100  [ QUARANTINED ]               │
│ Reason: Malicious prompt injection payload detected in body text stream.                        │
│ Status: QUARANTINED (Cannot advance in ATS)                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Candidate Deep-Dive & Cross-Product Transitions

1. **Ask SECUROXI about Candidate**: 1-click launch from the candidate drawer to pre-populate `/ask?q=What evidence supports this candidate experience&doc_id=CAND-ID&scope=candidates`.
2. **Inspect Document Evidence**: Opens [`/investigate`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/Investigation.tsx) with spatial bounding box overlay.
3. **Investigate in Security Brain**: For quarantined candidates, opens [`/security-brain`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/SecurityBrain.tsx) to inspect correlation graphs.
4. **Security Incident Link**: If candidate payload triggers a severe policy violation, links directly to the incident record in [`/incidents`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/Incidents.tsx).

---

## 5. ATS Connectors & Webhook Health

* **Supported Connectors**: Greenhouse Enterprise, Lever Talent Pipeline, Workday Sync, Custom Webhooks.
* **Telemetry**: Displays live connection status, verified HMAC signatures, and last synchronized timestamps without leaking client secrets.

---

## 6. Verification & Test Suite

* **Integration Suite**: [`tests/test_hiring_ats_experience.py`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/tests/test_hiring_ats_experience.py) validates candidate ingestion contracts, quarantine invariants, and fit score separation (`246 / 246 passed`).
* **Frontend Production Build**: `tsc && vite build` bundled in `1.25s`.
