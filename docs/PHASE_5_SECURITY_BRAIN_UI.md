# SECUROXI AI Phase 5 Stage 4 — Security Brain & Attack Graph Workspace Specification

**Engine Version**: `0.5.0-security-brain-ui`  
**Classification**: **`SECURITY BRAIN & ATTACK GRAPH WORKSPACE SPECIFICATION`**  
**Stage 4 Status**: **`PASS`**  
**Date**: `2026-08-14`

---

## 1. Security Brain Pipeline Architecture

The **SECUROXI Security Brain Workspace** (`/security-brain`) visualizes the complete threat correlation lifecycle using real backend data:

```
1. SIGNAL ──▶ 2. FORENSICS ──▶ 3. DETECTION ──▶ 4. ATTACK GRAPH ──▶ 5. AI REASONING ──▶ 6. POLICY DECISION ──▶ 7. ACTION & AUDIT
```

---

## 2. Attack Graph & Node-Edge Representation

* **Node 1: Actor / Sender Source**: Identifies untrusted origin (`UNTRUSTED_SENDER`, `API_CLIENT`, `ATS_WEBHOOK`).
* **Node 2: Artifact / File Payload**: Ingested document payload (e.g. `adversarial_resume.pdf`).
* **Node 3: Technique / Threat Signal**: Detected threat vector (`PROMPT_INJECTION`, `VISUAL_DECEPTION`, `EXFILTRATION_URL`).
* **Node 4: Target / Engine Boundary**: Target AI model pipeline or LLM context.
* **Node 5: Impact / Policy Enforcement**: Deterministic Policy Engine action (`BLOCK`, `QUARANTINE_DOCUMENT`).

---

## 3. Explicit AI Reasoning vs. Deterministic Policy Authority

The UI explicitly separates advisory LLM recommendations from authoritative Policy Engine enforcement:

| Component | Responsibility | Enforcement Authority |
| :--- | :--- | :--- |
| **AI Reasoning Layer** | Generates advisory contextual analysis & risk explanations | **Advisory Only (Non-Authoritative)** |
| **Deterministic Policy Engine** | Evaluates rules, risk thresholds, and enforces response actions | **100% Authoritative (Enforced)** |

---

## 4. Empirical Test Results (171 Tests)

```text
======================= 171 passed in 2.09s ========================
```
* **Real API Telemetry**: `Connected to /api/v1/brain/incidents & /scans` 🟢
* **Attack Graph Visualizer**: `Node-edge relationship rendering active` 🟢
* **AI vs. Policy Distinction**: `LLM Advisory vs Policy Enforced explicitly rendered` 🟢
* **Backend API Compatibility**: `171 / 171 Backend Security Tests Passed (100%)` 🟢

---

## 5. Stage 4 Status

# **`PASS`**
