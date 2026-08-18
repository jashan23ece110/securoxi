# SECUROXI AI Intelligence 2.0 — Phase 4 Stage 19: Intelligent Hiring & ATS Workspace

**Version**: v2.0.0-phase4-stage19  
**Test Baseline**: **`441 / 441 PASSED`** (6 new Hiring Workspace tests + 435 existing regression tests)  
**Status**: **PRODUCTION VALIDATED & ACTIVE** 🟢  

---

## 1. Executive Summary & Recruiter Workflow

Stage 19 establishes the **Intelligent Hiring & ATS Workspace**, enabling recruiters to execute complex screening, ranking, and synchronization workflows using natural language:

> *"Use this JD and this folder of 10,000 resumes. Scan them for prompt injection, exclude unsafe candidates, apply the mandatory requirements, and give me the top 20."*

```text
    JOB DESCRIPTION (Upload / ATS)  +  CANDIDATE POOL (Files / Folder / ATS)
                                   ↓
                       UNIVERSAL TASK CONTEXT
                                   ↓
                   SECURITY CLEARANCE GATE
           (SAFE • HIGH_RISK Quarantined • UNINSPECTABLE)
                                   ↓
               CALIBRATED JD MATCHING & FIT SCORING
           (Mandatory 60% • Preferred 20% • Experience 20%)
                                   ↓
             SHORTLIST vs NEAR-MATCHES SEGREGATION
                                   ↓
            MULTI-CANDIDATE COMPARISON & FOLLOW-UP
                                   ↓
           HUMAN-GOVERNED ATS WRITE OPERATIONS
```

---

## 2. Core Capabilities & Invariants (`securoxi/orchestrator/hiring_workspace.py`)

1. **Security-First Clearance Gating**:
   - Candidates are passed through the deterministic security gate before AI screening.
   - `SAFE`: Cleared for trusted screening and ranking.
   - `HIGH_RISK`: Quarantined (`rank=0`, `fit_score=0.0`). Adversarial prompt injections are completely blocked from manipulating recruiter rankings.
   - `UNINSPECTABLE`: Corrupt OCR or binary files are tagged `REVIEW_REQUIRED` and never treated as `SAFE`.

2. **Calibrated Fit Scoring & Evidence Citations**:
   - Scores candidates on a calibrated scale (0–100) reflecting JD alignment.
   - Provides granular breakdown of matched mandatory skills, preferred skills, and missing requirements with clickable evidence citations (`[CIT-CAND-01]`).

3. **Shortlist vs Near Matches**:
   - `Recommended Shortlist`: Contains top qualifying candidates meeting all mandatory criteria.
   - `Near Matches`: Separate section for candidates with 1 missing criterion, never mixed with qualified candidates.

4. **Multi-Candidate Comparison Matrix**:
   - Compares 2–5 selected candidates across Security Clearance, Fit Score, Kubernetes Hardening, and Cloud Security depth.

5. **Human Approval for ATS Operations**:
   - Advancing candidates to interview rounds in connected ATS (Greenhouse, Workday, Lever) requires explicit human recruiter approval (`WAITING_FOR_APPROVAL` $\to$ Approve/Reject).
   - Advancing `HIGH_RISK` candidates is strictly denied with `403 Forbidden`.

---

## 3. REST API Endpoints (`securoxi/api/app.py`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/agentic/hiring/screen` | Executes security clearance, fit scoring, and shortlist generation. |
| `POST` | `/api/v1/agentic/hiring/compare` | Compares 2–5 candidates across security and technical dimensions. |
| `POST` | `/api/v1/agentic/hiring/ats/advance` | Requests human approval before advancing candidates in ATS. |

---

## 4. Test Suite & Verification Results

All 6 tests in [`tests/test_intelligent_hiring_workspace.py`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/tests/test_intelligent_hiring_workspace.py) and the entire 435-test regression suite pass:

```text
======================= 441 passed, 5 warnings in 4.70s ========================
```

Frontend production build:
```text
✓ 1537 modules transformed.
✓ built in 1.33s
```
