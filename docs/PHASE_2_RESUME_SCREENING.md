# SECUROXI AI Phase 2 — Security-Aware Resume-to-JD Screening System

**Engine Version**: `0.2.0-phase2`  
**Classification**: **`PRODUCTION CANDIDATE`**  
**Phase 2 Status**: **`PASS`**

---

## 1. System Architecture

```
                                [Untrusted Candidate Resume PDF]
                                               |
                                               v
                        +----------------------------------------------+
                        |  Phase 1 Mandatory Security Scan Gate        |
                        |  - Visual Deception Analyzer (Micro/White)   |
                        |  - Prompt Injection Analyzer (Overrides/ATS) |
                        |  - AI Security Reasoning Layer               |
                        +----------------------------------------------+
                                               |
                     +-------------------------+-------------------------+
                     | (Verdict Check)                                   |
                     v                                                   v
           [Verdict: HIGH_RISK]                                [Verdict: SAFE / SUSPICIOUS]
                     |                                                   |
                     v                                                   v
      +-----------------------------+                     +-----------------------------+
      |  QUARANTINE SECURITY GATE   |                     | Phase 2 Screening Pipeline  |
      |  - Fit Score: 0.0           |                     | 1. Structured Ingestion     |
      |  - Recommendation: BLOCKED  |                     | 2. Profile Extraction       |
      |  - Security Report Attached |                     | 3. Skill Normalization      |
      +-----------------------------+                     | 4. Requirement Matching     |
                                                          | 5. Experience Qualification |
                                                          | 6. Explainable Fit Scoring  |
                                                          | 7. Report Generation        |
                                                          +-----------------------------+
                                                                         |
                                                                         v
                                                             [ScreeningReport (JSON/MD)]
```

---

## 2. Core Capabilities & Stage Summary

1. **Stage 1 — Ingestion Infrastructure**: Distinguishes `RESUME` vs `JOB_DESCRIPTION`, enforcing Phase 1 Security Scanning on all untrusted resume inputs before document section partitioning.
2. **Stage 2 — Structured Extraction**: Extracts candidate profiles (`candidate_name`, `summary`, `skills`, `education`, `work_experience`, `projects`) and JD profiles (`job_title`, `required_skills`, `preferred_skills`, `minimum_experience_years`). Missing fields return `"UNKNOWN"` or `"NOT_SPECIFIED"`.
3. **Stage 3 — Skill Normalization**: Maps raw skill aliases (`JS` $\rightarrow$ `JavaScript`, `K8s` $\rightarrow$ `Kubernetes`, `Golang` $\rightarrow$ `Go`) while preserving strict distinction rules (`C` $\neq$ `C++` $\neq$ `C#`, `Java` $\neq$ `JavaScript`).
4. **Stage 4 — Requirement-Level Matching Engine**: Evaluates `EXACT_MATCH`, `NORMALIZED_MATCH`, `SEMANTIC_RELATED` (e.g. `PostgreSQL` vs `MySQL`), and `NO_MATCH`. Strict distinction prevents over-generalization (`React` vs `React Native` $\rightarrow$ `NO_MATCH`).
5. **Stage 5 — Qualification & Experience Analysis**: Merges overlapping employment date intervals (`2020-2023` & `2022-2025` $\rightarrow$ `5.0 yrs`), separates total career length from technology-specific experience, and checks degree/certification compliance.
6. **Stage 6 — Candidate Fit Scoring & Ranking**: Calculates explainable fit scores (`EXCELLENT_FIT`, `STRONG_FIT`, `PARTIAL_FIT`, `WEAK_FIT`). Enforces a **Mandatory Missing Skill Penalty Ceiling (`50.0`)**, ensuring candidates missing required skills cannot score above 50.0 regardless of total career length.
7. **Stage 7 — Explainable Screening Reports**: Generates machine-readable JSON and human-readable Markdown screening reports (`to_markdown()`) with line-by-line evidence provenance and mandatory human review legal disclaimers.
8. **Stage 8 — Security-Aware Screening Pipeline**: Enforces Phase 1 Security Scanning as a mandatory gate. Malicious high-risk resumes are quarantined at rank #0 with score `0.0`. **Security always wins!**

---

## 3. Policy Decisions & Attack Resilience

* **`SAFE` Policy**: Automated screening proceeds normally.
* **`SUSPICIOUS` Policy**: Screening proceeds with `requires_human_security_review: true` flag and security warning banner.
* **`HIGH_RISK` Policy**: Automated screening is **BLOCKED**. Report returns `fit_score = 0.0`, category = `INSUFFICIENT_DATA`, candidate_name = `QUARANTINED: <filename>`, and attaches complete Phase 1 security report.

---

## 4. Empirical Test Suite Results (88 Tests)

```text
======================== 88 passed in 0.72s ========================
```
* **Phase 1 Security & System Tests**: `57 / 57 PASSED`
* **Phase 2 Ingestion & Extraction Tests**: `8 / 8 PASSED`
* **Phase 2 Normalization & Matching Tests**: `10 / 10 PASSED`
* **Phase 2 Qualification & Scoring Tests**: `7 / 7 PASSED`
* **Phase 2 Report & Security Pipeline Tests**: `6 / 6 PASSED`
* **Total Suite**: **`88 / 88 PASSED (100%)`**

---

## 5. Phase 2 Final Status

# **`PASS`**

**Summary**:  
SECUROXI AI Phase 2 delivers an enterprise-grade, security-aware Resume-to-JD screening and ranking system. It guarantees that untrusted candidate resumes pass Phase 1 security inspection before screening, prevents prompt injection manipulation, normalizes skill taxonomies, calculates non-overlapping experience, caps fit scores for missing required skills, produces explainable provenance reports, and passes **`88 / 88 automated unit and integration tests`**.
