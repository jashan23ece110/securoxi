# SECUROXI AI — UI/UX Stage 7: Candidate Screening & Recruiting Security Workspace Specification

**Stage**: UI/UX Stage 7 — Resume Screening Workspace  
**Status**: Verified & Operational  
**Test Baseline**: `226 / 226 PASSED` (in 2.42s)  
**Frontend Compilation**: `tsc && vite build` $\rightarrow$ `built in 806ms`  
**Route**: `/screening` (Component: [`ScreeningPage.tsx`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/Screening.tsx))

---

## 1. Executive Summary & Recruiting Security Philosophy

The `/screening` workspace bridges high-volume enterprise talent acquisition with deterministic AI defense. Built on top of the Phase 2 Screening and Qualification Engine, it enforces an unbreakable security boundary:

$$\text{Job Description (JD)} \longrightarrow \text{Candidate Ingestion} \longrightarrow \text{Security Clearance Gate} \longrightarrow \text{Qualification Matching} \longrightarrow \text{Fit Score} \longrightarrow \text{Evidence Traceability}$$

### The Security Clearance Invariant
> [!IMPORTANT]
> **Zero False Escapes on Malicious Candidates**:
> Resumes containing adversarial prompt injections or visual deceptions are marked `QUARANTINED` and frozen at **Rank #0**. The UI strictly prohibits advancing quarantined candidates to interview without explicit security review.

---

## 2. Workspace Architecture

```
+---------------------------------------------------------------------------------------------------------------+
|  HIRING / SCREENING WORKSPACE                                                                                 |
|  Candidate Screening & Recruiting Security Workspace          [ Refresh Pool ] [ Scan Candidate Resumes ]     |
|  Deterministic qualification matching, semantic fit scoring & strict security gate isolation                 |
+---------------------------------------------------------------------------------------------------------------+
|  +--------------------+ +--------------------+ +--------------------+ +------------------------------------+  |
|  | TOTAL CANDIDATES   | | SECURITY CLEARED   | | QUARANTINED THREATS| | STRONG FIT SHORTLIST               |  |
|  | 4                  | | 3 (75.0%)          | | 1 (25.0%)          | | 2                                  |  |
|  | Active pipeline    | | Verified clean     | | Security Gate Block| | Fit Score >= 85/100                |  |
|  +--------------------+ +--------------------+ +--------------------+ +------------------------------------+  |
+---------------------------------------------------------------------------------------------------------------+
|  [!] Calibrated Fit Score Notice: Scores represent qualification alignment, NOT automated hiring probability.  |
+---------------------------------------------------------------------------------------------------------------+
|  Search: [Filter candidate...]  Security: [All Statuses v]  Category: [All Categories v]  Showing 4 candidates    |
|  -----------------------------------------------------------------------------------------------------------  |
|  Rank   | Candidate & Role       | Security Clearance | Calibrated Fit Score | Matched Skills   | Actions     |
|  #1     | Alex Rivera            | [🟢 CLEARED]       | [=======] 94.2 / 100 | Python, K8s, CI  | [ Inspect ] |
|  #2     | Elena Rostova          | [🟢 CLEARED]       | [====== ] 86.5 / 100 | Python, Go, SIEM | [ Inspect ] |
|  BLOCKED| Adversarial Payload    | [🚨 QUARANTINED]   | [       ]  0.0 / 100 | (Blocked)        | [ Inspect ] |
+---------------------------------------------------------------------------------------------------------------+
```

---

## 3. Deep Candidate Inspection Drawer & Grounded RAG Provenance

Clicking **"Inspect"** opens the candidate inspection drawer ([`Drawer.tsx`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/components/ui/Drawer.tsx)), presenting three structured verification layers:

### Layer 1: Qualifications & Requirement Gap Matrix
* Matched required skills (e.g. `✓ Python`, `✓ Kubernetes`, `✓ Cloud Security`).
* Missing mandatory requirements (e.g. `✕ Terraform IaC`).
* Verified education history and industry certifications (`CISSP`, `AWS Security Specialty`).

### Layer 2: Three-Tier Grounded Evidence (RAG Provenance)
1. **EXTRACTED RESUME FACTS (Deterministic Source)**:
   * Direct text extractions from candidate PDF/DOCX.
2. **SEMANTIC VECTOR MATCH (pgvector Embeddings)**:
   * 384-dimensional cosine distance similarity scores (e.g. `0.912 cosine match` against core competencies).
3. **LLM REASONING & SUMMARY (Advisory Context)**:
   * Qualitative qualification synthesis explaining candidate strengths without overriding security verdicts.

### Layer 3: Security Gate Provenance
* Immutable HMAC audit signature, evaluated policy rule ID (`RULE-090-PROMPT-INJECTION-QUARANTINE`), and gate status.

---

## 4. Verification & Quality Assurance

* **TypeScript & Vite Build**: `✓ built in 806ms` (0 errors).
* **Backend Pytest Suite**: `226 passed, 5 warnings in 2.42s` (100% pass rate).
* **Security Gate Enforcement**: Quarantined candidates cannot bypass clearance or advance to technical screening.
