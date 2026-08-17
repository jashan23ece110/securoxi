# SECUROXI AI — Security Brain & Advanced Investigation Experience

**Module**: Security Brain Advanced Threat Intelligence & Causality  
**Component**: [`SecurityBrainPage.tsx`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/SecurityBrain.tsx)  
**Backend Endpoints**: `GET /api/v1/incidents`, `GET /api/v1/scans`  
**Route**: `/security-brain`  
**Test Baseline**: `249 / 249 PASSED` (in 3.28s)  
**Frontend Compilation**: `tsc && vite build` $\rightarrow$ `✓ built in 1.29s`  
**Status**: Verified & Operational  

---

## 1. Executive Summary

The **Security Brain** is SECUROXI's advanced threat correlation and investigation engine. It models the causal chain of security events and enforces a strict separation between empirical forensic evidence, probabilistic AI reasoning, and deterministic policy authority:

```text
SIGNAL ──► FORENSICS ──► DETECTION ──► CONTEXT ──► CORRELATION ──► ATTACK GRAPH ──► AI ADVISORY ──► RISK ──► POLICY ──► ACTION ──► AUDIT
```

---

## 2. Investigation Modes

### A. Guided Investigation Mode (Default for Security Users)
Presents a linear, prioritized causality walkthrough without graph complexity:
1. **Threat Context**: Investigating Threat, Affected Asset, Ingress Origin, Risk Gauge (0–100).
2. **Empirical Forensic Evidence (Observed Fact)**: Raw unmanipulated text payload and layout anomaly detected by parser engine.
3. **AI Advisory Interpretation**: Probabilistic reasoning summary (explicitly non-authoritative).
4. **Policy Authority & Enforcement**: Deterministic rule outcome (`RULE-100-HIGH-RISK-BLOCK` $\to$ `BLOCK + QUARANTINE`).
5. **Mitigation Actions**: 1-click navigation to Forensic Viewer, Incident Response, or Ask SECUROXI.

### B. Advanced Investigation Mode (For SOC Analysts)
Provides an interactive 3-column workspace with a real Attack Graph:
* **Left**: Telemetry stream of correlated findings with search and risk filters.
* **Center**: Interactive Attack Graph with zoom in/out/reset, panning, and node selection (`ACTOR`, `ARTIFACT`, `SIGNAL`, `TECHNIQUE`, `TARGET`, `IMPACT`).
* **Right**: Real-time Node Inspector and Policy Decision Telemetry.

---

## 3. Strict Three-Layer Decision Model

| Layer | Responsibility | Authority | Example |
| :--- | :--- | :---: | :--- |
| **1. Forensic Evidence** | Empirical facts extracted from document layout & text | **Observed Fact** | Raw micro-text payload `font_size: 2.5pt` |
| **2. AI Advisory** | LLM probabilistic reasoning & intent interpretation | **Advisory Only** | *"Evidence consistent with indirect prompt injection."* |
| **3. Policy Authority** | Deterministic SECUROXI Policy Engine evaluation | **Enforced Authority** | `RULE-100-HIGH-RISK-BLOCK` $\to$ `BLOCK` |

> **Critical Security Invariant**: **`AI ADVISORY ≠ POLICY AUTHORITY`**. The UI visually reinforces that LLM reasoning is advisory and cannot override deterministic policy rules.

---

## 4. Resilience & Fallback Invariants

* **LLM Layer Unavailable**: If LLM reasoning is offline, the Security Brain continues functioning seamlessly. Forensic evidence, risk scores, deterministic policy decisions, and audit trails remain 100% operational.
* **Graph Rendering Unavailable**: If graph telemetry is unavailable, the interface defaults to text-based causal steps and timeline logs.

---

## 5. Cross-Product Investigation Links

* **Inspect on Document Canvas**: Launches [`/investigate/:scanId`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/Investigation.tsx) with spatial bounding box overlays.
* **Ask SECUROXI about Threat**: Launches [`/ask`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/AskSecuroxi.tsx) scoped to the threat context.
* **View Linked Incident**: Launches [`/incidents`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/Incidents.tsx) with the incident record selected.
* **Configure Policies**: Launches [`/policies`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/Policies.tsx).

---

## 6. Verification & Test Suite

* **Integration Suite**: [`tests/test_security_brain_investigation.py`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/tests/test_security_brain_investigation.py) validates incident telemetry, the 3-layer decision hierarchy, and deterministic policy fallback (`249 / 249 passed`).
* **Frontend Production Build**: `tsc && vite build` bundled cleanly in `1.29s`.
