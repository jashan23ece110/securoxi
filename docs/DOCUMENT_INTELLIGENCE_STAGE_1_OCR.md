# SECUROXI AI — Document Intelligence Stage 1: OCR & Uninspectable Document Security Specification

**Engine Version**: `0.6.0-doc-intel-ocr`  
**Classification**: **`DOCUMENT INTELLIGENCE & SECURITY SPECIFICATION`**  
**OCR Engine**: **`Modular PyMuPDF Pixmap Renderer + Tesseract Fallback`**  
**Date**: `2026-08-15`

---

## 1. Modular OCR Architecture & Fallback Flow

```
                     [PDF Document Input]
                              │
                    (Native Text Extraction)
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
      [Sufficient Native Text]    [Insufficient Native Text (<10 Chars)]
                 │                         │
                 │                 (Render Page Pixmap)
                 │                         │
                 │                [OCREngine Fallback]
                 │                         │
                 ▼                         ▼
         source="NATIVE_PDF"           source="OCR"
                 │                         │
                 └────────────┬────────────┘
                              ▼
                [Total Text Spans Evaluated]
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
         [Spans Count > 0]         [Spans Count == 0]
                 │                         │
       (Standard Security Scan)   (UNINSPECTABLE SAFETY GUARD)
                 │                         │
                 ▼                         ▼
      Status: ANALYZED / OCR    Status: UNINSPECTABLE
      Verdict: SAFE / HIGH      Verdict: SUSPICIOUS (Score 40)
```

---

## 2. Document Analysis States & Security Policy

| Analysis Status | Definition | Default Security Verdict | Screening Gate Action |
| :--- | :--- | :--- | :--- |
| **`ANALYZED`** | Native text extracted and forensic visual analysis completed. | Evaluated by Risk Engine (`SAFE` / `SUSPICIOUS` / `HIGH_RISK`) | Normal automated screening if `SAFE`. |
| **`ANALYZED_WITH_OCR`** | Native text was insufficient; OCR fallback extracted text spans. | Evaluated by Risk Engine (`SAFE` / `SUSPICIOUS` / `HIGH_RISK`) | Normal automated screening with `source="OCR"` provenance log. |
| **`PARTIALLY_ANALYZED`**| Document contains mixed native text and OCR-extracted image content. | Evaluated by Risk Engine | Normal automated screening with provenance log. |
| **`UNINSPECTABLE`** | **Zero inspectable text spans extracted after native & OCR attempts.** | **`SUSPICIOUS` (Risk Score 40)** | **QUARANTINED AT RANK #0 (Fit Score 0.0).** |

---

## 3. Critical Security Guarantee

# **Zero Uninspectable Document Rule**
> **No document that SECUROXI failed to inspect may EVER be classified as `SAFE`.**  
> An image-only or scanned PDF yielding zero inspectable text spans is assigned `analysis_status = UNINSPECTABLE`, `Verdict = SUSPICIOUS` (Risk Score 40), and quarantined by the Phase 2 Resume Security Clearance Gate.

---

## 4. Empirical Test Results (204 Tests)

```text
======================= 204 passed in 2.38s ========================
```
* **Existing Test Suite (Phases 1-5, Infrastructure & Production)**: `198 / 198 PASSED (0 Regressions)` 🟢
* **New OCR & Uninspectable Document Security Tests**: `6 / 6 PASSED` 🟢
* **Total Test Suite**: **`198 + 6 = 204 / 204 PASSED (100%)`** 🟢

---

## 5. Status Decision Choice

# **`PASS`**
