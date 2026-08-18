# SECUROXI AI Intelligence 2.0 — Phase 4 Stage 20: Agentic RAG + Ask SECUROXI Grounded Research Workspace

**Version**: v2.0.0-phase4-stage20  
**Test Baseline**: **`448 / 448 PASSED`** (7 new Ask SECUROXI tests + 441 existing regression tests)  
**Status**: **PRODUCTION VALIDATED & ACTIVE** 🟢  

---

## 1. Executive Summary & Core Research Paradigm

Stage 20 delivers the **Agentic RAG + Ask SECUROXI Grounded Research Workspace**, transforming question answering and document exploration into an evidence-grounded research environment across authorized documents, candidate collections, folders, JDs, and prior task contexts:

> *"I can ask SECUROXI anything about the information I am authorized to use."*

```text
       USER RESEARCH QUERY  +  UNIVERSAL CONTEXT (Doc / Folder / Pool)
                                    ↓
                       AUTOMATIC MODE INFERENCE
       (Direct Answer • Research • Comparison • Summary • Ranking)
                                    ↓
                     CANONICAL PHASE 3 AGENTIC RAG
  (Strategy → Adaptive Multi-Hop → Fusion → Verification → Synthesis)
                                    ↓
                       GROUNDED RESEARCH OUTCOME
 (Answer • Key Findings • Citations • Conflicts • Suggested Follow-ups)
```

---

## 2. Core Capabilities & Architectural Invariants (`securoxi/orchestrator/ask_workspace.py`)

1. **Automatic Research Mode Inference**:
   - Automatically classifies queries without forcing users into complex mode selection:
     - `Compare Sarah vs David` $\to$ `SynthesisMode.COMPARISON`.
     - `Why is candidate #1?` $\to$ `SynthesisMode.RANKING_EXPLANATION`.
     - `Analyze skill gaps across resumes` $\to$ `SynthesisMode.RESEARCH`.
     - `Summarize policy` $\to$ `SynthesisMode.SUMMARY`.
     - `Direct question` $\to$ `SynthesisMode.DIRECT_ANSWER`.

2. **Honest Groundedness & No-Evidence Handling**:
   - Differentiates `FULLY_GROUNDED`, `GROUNDED_WITH_QUALIFICATIONS`, `PARTIAL`, and `NO_EVIDENCE`.
   - Never hallucinates answers when data is missing: outputs honest explanation (*"I couldn't find supporting evidence in the authorized sources."*) along with suggested search refinement actions.

3. **Validated Forensic Citations**:
   - Each claim is mapped to verified citations (`[CIT-1]`) with document IDs, chunk references, and clickable links to the existing forensic document viewer.

4. **Multi-Scope Exploration**:
   - Scopes queries to `CURRENT_DOCUMENT`, `FOLDER`, `CANDIDATE_SET`, `JOB_DESCRIPTION`, or `TENANT_COLLECTION` without silent scope expansion.

5. **Follow-Up Context Continuity**:
   - Natural language follow-up queries retain prior verified evidence, citations, and attached context without requiring users to re-select documents.

---

## 3. REST API Endpoints (`securoxi/api/app.py`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/agentic/ask` | Executes grounded conversational research query through Agentic RAG. |

---

## 4. Test Suite & Verification Results

All 7 tests in [`tests/test_ask_securoxi_workspace.py`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/tests/test_ask_securoxi_workspace.py) and the entire 441-test regression suite pass:

```text
======================= 448 passed, 5 warnings in 4.74s ========================
```

Frontend production build:
```text
✓ 1537 modules transformed.
✓ built in 1.39s
```
