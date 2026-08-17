# SECUROXI AI — Ask SECUROXI / Secure Document Intelligence Experience

**Module**: Ask SECUROXI / Secure Document Intelligence  
**Component**: [`AskSecuroxiPage.tsx`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/AskSecuroxi.tsx)  
**Backend Endpoint**: `POST /api/v1/ask` $\longrightarrow$ [`SecuroxiRAGEngine`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/securoxi/screening/rag_engine.py)  
**Route**: `/ask`  
**Test Baseline**: `243 / 243 PASSED` (in 3.31s)  
**Frontend Compilation**: `tsc && vite build` $\rightarrow$ `✓ built in 1.26s`  
**Status**: Verified & Operational  

---

## 1. Executive Summary

The **Ask SECUROXI Document Intelligence Experience** simplifies enterprise document search and question answering by hiding complex engineering internals (vector databases, 384-dimensional embeddings, chunk splits, and context window limits) behind a single, intuitive workflow:

> **Ask Question** $\longrightarrow$ **Secure Verified Search** $\longrightarrow$ **Grounded Answer** $\longrightarrow$ **Click Citation to View Forensic Document**

---

## 2. Secure Retrieval & Grounded Intelligence Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ USER NATURAL-LANGUAGE QUERY (e.g. "Which candidates have Kubernetes & cloud security?")         │
└────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ MULTI-TENANT & QUARANTINE SECURITY FILTER                                                       │
│                                                                                                 │
│  • Tenant Validation: Strict isolation by X-Tenant-ID                                           │
│  • Security Quarantine Filter: Excludes HIGH_RISK, CRITICAL, and UNINSPECTABLE chunks           │
│  • Fenced Evidence Assembly: Retrieved text enclosed in <evidence_item> blocks to prevent      │
│    indirect prompt injection payloads from hijacking LLM execution                              │
└────────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ GROUNDED ANSWER & CITATION ENGINE                                                               │
│                                                                                                 │
│  • Natural-Language Response grounded strictly in retrieved facts                               │
│  • Groundedness Score & Latency Telemetry                                                       │
│  • Clickable Citations [Doc: resume_01.pdf, Page: 2] linking directly to the Forensic Viewer    │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Four-Stage Progressive UX (Without Jargon)

When querying, users see a simple reassuring four-stage progress indicator:

1. **✓ 1. Authorizing Access**: Verifies user tenant and document permission scopes.
2. **✓ 2. Searching Documents**: Scans authorized candidate and document repositories.
3. **✓ 3. Verifying Quarantine Filters**: Ensures malicious or uninspectable content is quarantined.
4. **✓ 4. Building Grounded Answer**: Synthesizes facts with clickable document citations.

---

## 4. Citation $\longrightarrow$ Forensic Document Viewer Integration

Every substantive claim includes clickable citation badges:

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ QUESTION: "Which candidates have production Kubernetes experience?"                             │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ANSWER: "Alex Rivera and Elena Rostova demonstrate extensive production Kubernetes experience,  │
│ managing container security pipelines across 4,000+ cluster nodes."                             │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ SUPPORTING CITATIONS:                                                                           │
│ [ CAND-ALEX-RIVERA • Page 1 • Relevance: 96% → ]                                                │
│ [ CAND-ELENA-ROSTOVA • Page 2 • Relevance: 91% → ]                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

* Clicking any citation navigates directly to [`/investigate/:scanId`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/Investigation.tsx) or launches the **Forensic Document Viewer**, centering the viewport on the exact page and evidence coordinates.

---

## 5. Security & Invariant Guarantees

1. **Quarantine Exclusion**: `HIGH_RISK` and `UNINSPECTABLE` files are strictly excluded from default trusted answer context (`include_quarantined=False`).
2. **Anti-Prompt Injection Defense**: Retrieved evidence is fenced inside XML boundaries with instruction-data isolation, preventing embedded adversarial text from altering system instructions.
3. **Honest Groundedness**: If documents lack sufficient evidence, SECUROXI states: *"No verified document evidence found in tenant repository to answer the query."* (Zero hallucinations or fabricated citations).
4. **Credential Boundary**: LLM and vector store secrets never leak to browser clients; all requests pass through authenticated backend proxying.

---

## 6. Verification & Test Suite

* **Integration Suite**: [`tests/test_ask_securoxi_intelligence.py`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/tests/test_ask_securoxi_intelligence.py) validates grounded Q&A contracts, multi-tenant boundaries, and quarantine exclusion (`243 / 243 passed`).
* **Frontend Production Build**: `tsc && vite build` bundled in `1.26s`.
