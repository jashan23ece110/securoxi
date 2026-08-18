# SECUROXI AI Intelligence 2.0 — Phase 4 Stage 21: Security Investigation & Evidence Workspace

**Version**: v2.0.0-phase4-stage21  
**Test Baseline**: **`455 / 455 PASSED`** (7 new Security Investigation tests + 448 existing regression tests)  
**Status**: **PRODUCTION VALIDATED & ACTIVE** 🟢  

---

## 1. Executive Summary & Investigator Paradigm

Stage 21 creates the **Security Investigation & Evidence Workspace**, unifying the end-to-end security investigation workflow:

> Detection $\to$ Evidence $\to$ Investigation $\to$ Security Brain $\to$ Attack Chain $\to$ Policy $\to$ Incident $\to$ Controlled Response

```text
    SECURITY DETECTION (Scanner / Brain / Alert)
                        ↓
            INITIALIZE INVESTIGATION
  (Subject • Document • Security Status • Findings)
                        ↓
         SYNCHRONIZED EVIDENCE & DOCUMENT
    (Page • Bounding Box • Section • Highlighting)
                        ↓
       CONTEXTUAL SECURITY BRAIN ATTACK CHAINS
        (Observed Steps vs Inferred Hypotheses)
                        ↓
         AUTHORITATIVE POLICY & TIMELINE
         (Policy P-100: BLOCK • Audit Trail)
                        ↓
        SCOPED Q&A & HUMAN-GOVERNED ACTIONS
 (Quarantine Batch • Block • Create Incident Approval)
```

---

## 2. Core Capabilities & Architectural Invariants (`securoxi/orchestrator/security_investigation_workspace.py`)

1. **Synchronized Evidence ↔ Document Viewer**:
   - Every investigated finding maintains precise document layout provenance (`page`, `bbox`, `section`).
   - Selecting a finding navigates directly to the highlighted document location in the existing forensic viewer.

2. **Contextual Security Brain & Attack Chains**:
   - Constructs structured multi-step attack graphs (`ForensicAttackChain`).
   - Distinguishes **OBSERVED** steps (e.g. zero-font payload in body) from **INFERRED** hypotheses (e.g. intent to override ranking).

3. **Authoritative Policy State & Real Audit Timelines**:
   - Enforces enterprise security policy (`Policy: P-100`, `State: BLOCKED`) as immutable from UI/agents.
   - Generates real timelines from authoritative audit/detection events.

4. **Human-Governed Response Actions**:
   - High-impact response actions (`QUARANTINE_BATCH`, `BLOCK_SENDER`, `RESOLVE_INCIDENT`) require explicit human approval via the `AutonomousExecutionRunner` gate (`WAITING_FOR_APPROVAL`).

5. **Scoped Investigation Q&A with Explicit Scope Expansion**:
   - Natural-language queries are scoped to the active investigation findings.
   - Broadening requests (*"Find similar attacks across all candidates"*) trigger explicit analyst confirmation (`SCOPE_EXPANSION_REQUIRED`) before searching organization-wide data.

6. **Structured User Notes & Confidential Exports**:
   - User notes are labeled `USER_NOTE` and never mutate authoritative security verdicts.
   - Generates exportable investigation reports with provenance, citations, and classification tags.

---

## 3. REST API Endpoints (`securoxi/api/app.py`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/agentic/investigation/create` | Initializes a new structured investigation context. |
| `GET` | `/api/v1/agentic/investigation/{id}` | Retrieves full investigation state with tenant isolation. |
| `POST` | `/api/v1/agentic/investigation/{id}/note` | Adds a structured user note (`USER_NOTE`). |
| `POST` | `/api/v1/agentic/investigation/{id}/action` | Requests high-impact response action with human approval. |
| `POST` | `/api/v1/agentic/investigation/{id}/ask` | Executes scoped investigation Q&A. |
| `GET` | `/api/v1/agentic/investigation/{id}/export` | Exports confidential investigation report. |

---

## 4. Test Suite & Verification Results

All 7 tests in [`tests/test_security_investigation_workspace.py`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/tests/test_security_investigation_workspace.py) and the entire 448-test regression suite pass:

```text
======================= 455 passed, 5 warnings in 5.08s ========================
```

Frontend production build:
```text
✓ 1537 modules transformed.
✓ built in 1.34s
```
