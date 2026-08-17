# SECUROXI AI — Smart Results & Security Distribution Experience

**Module**: Smart Results & Security Distribution  
**Components**: [`SmartResultTable.tsx`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/components/results/SmartResultTable.tsx), [`SecurityDistributionBar.tsx`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/components/results/SecurityDistributionBar.tsx)  
**Export Endpoint**: `GET /api/v1/scans/export?format=csv|json`  
**Test Baseline**: `237 / 237 PASSED` (in 3.28s)  
**Frontend Compilation**: `tsc && vite build` $\rightarrow$ `✓ built in 1.30s`  
**Status**: Verified & Operational  

---

## 1. Executive Summary

The **Smart Results & Security Distribution Experience** transforms complex security scan outputs into an intuitive classification surface. Users immediately understand:
1. **How many files were analyzed?**
2. **How many are safe vs require attention?**
3. **Which files are high-risk and why were they flagged?**
4. **What exact actions to take next.**

---

## 2. Action Priority & Invariant Hierarchy

SECUROXI enforces a strict priority hierarchy that guides analyst attention to the most critical threats first:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ ACTION PRIORITY ORDER                                                             │
├─────┬──────────────────┬─────────────────────────────────────────────────────────┤
│ #   │ CLASSIFICATION   │ UX ACTION & CALLOUT                                     │
├─────┼──────────────────┼─────────────────────────────────────────────────────────┤
│ 1   │ HIGH RISK        │ 🔴 Dominates attention. Immediate quarantine alert.     │
│ 2   │ UNINSPECTABLE    │ 🟠 Quarantined raster. Explicit warning: UNINSP != SAFE │
│ 3   │ SUSPICIOUS       │ 🟡 Needs investigation for visual concealment / micro   │
│ 4   │ FAILED           │ ⚪ Non-security system error with 1-click retry         │
│ 5   │ SAFE             │ 🟢 Clean verification with compact badge                │
└─────┴──────────────────┴─────────────────────────────────────────────────────────┘
```

---

## 3. Visual Proportional Distribution (`SecurityDistributionBar.tsx`)

A segmented bar visualization displays proportional ratios across all documents with interactive click-to-filter states:

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ [!] 392 documents require attention                                    [ Review High Risk → ] │
│ 392 High Risk • 211 Uninspectable • 841 Suspicious • 16,932 Clean Passed                      │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ [████ HIGH RISK 2.1% ][██ UNINSP 1.2% ][████ SUSP 4.7% ][████████████████████ SAFE 91.5% ]   │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. User-Friendly Plain-Language Threat Translation

Technical detector names and regex classifications are translated into clear, human-understandable summaries:

| Raw Technical Category | User-Facing Plain Language Summary |
| :--- | :--- |
| `PROMPT_INJECTION` | *Instruction detected attempting to manipulate automated workflow* |
| `MICRO_TEXT` | *Concealed micro text with font size below readability threshold* |
| `WHITE_TEXT` / `BACKGROUND_MATCH` | *Text styled to blend into background for visual concealment* |
| `ATS_MANIPULATION` | *Adversarial override attempting to force keyword pass* |
| `OCR_PAYLOAD` | *Suspicious payload detected in scanned image layer* |
| `UNICODE_OBFUSCATION` | *Hidden or invisible unicode characters detected* |
| `CLEAN_PASS` | *Security analysis complete. Zero threats detected.* |

---

## 5. Candidate ATS Screening: Security vs Fit Separation

In candidate recruitment workflows, security clearance is kept strictly separate from candidate qualification fit scores:

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ CANDIDATE: Sarah Miller                                                                      │
│ Security Clearance: [ SAFE ]                Candidate Fit Score: 94 / 100 [ STRONG FIT ]     │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│ CANDIDATE: Adversarial Resume                                                                │
│ Security Clearance: [ HIGH RISK ] (Blocked) Candidate Fit Score: 0 / 100  [ QUARANTINED ]    │
│ Reason: Malicious prompt injection payload detected in body text stream.                     │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Real-Time Search, Filtering, and Pagination

* **Search**: Sub-millisecond filtering by file name, scan ID, or plain-language summary.
* **Pagination**: Memory-bounded slicing (`10`, `25`, `50`, `100` items per page) prevents browser DOM degradation across large datasets.
* **Export**: Direct download of verified scan inventories as scoped CSV (`/api/v1/scans/export?format=csv`) or JSON (`/api/v1/scans/export?format=json`).

---

## 7. Verification & Test Suite

* **Unit & Integration Suite**: [`tests/test_smart_results_distribution.py`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/tests/test_smart_results_distribution.py) validates CSV/JSON export endpoints, priority ranking invariants, and candidate security separation (`237 / 237 passed`).
* **Frontend Production Build**: `tsc && vite build` bundled cleanly in `1.30s`.
* **Authoritative Preservation**: Core engines remain unchanged.
