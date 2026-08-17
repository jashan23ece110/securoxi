# SECUROXI AI Phase 4 Stage 5 — Malicious Document & Parser Security Specification

**Engine Version**: `0.4.0-document-hardening`  
**Classification**: **`ENTERPRISE DOCUMENT SECURITY & PARSER SPECIFICATION`**  
**Stage 5 Status**: **`PASS`**  
**Date**: `2026-08-14`

---

## 1. Document & Parser Security Architecture

The **SECUROXI Document Security & Parser Layer** implements multi-layered safeguards against decompression bombs, ZipSlip path traversal, malformed PDF crashes, and resource exhaustion:

```
[Uploaded Document / ZIP Archive]
                 ↓
  1. ZipSlip Prevention: Canonical path checks (`target.startswith(extract)`)
  2. ZIP Entry Limit: Max 50 files per archive
  3. Compression Ratio Limit: Max 100:1 ratio check
  4. Decompression Size Limit: Max 50 MB total uncompressed size
                 ↓
      [Safely Extracted PDF File]
                 ↓
  5. File Size Limit: Max 10 MB per PDF document
  6. Page Limit: Max 50 pages processed per PDF
  7. Text Span Limit: Max 10,000 text spans processed
  8. Magic Byte & Parser Exception Handling (`ValueError` on corruption)
                 ↓
   [Layout-Aware TextSpans Passed to Security Brain]
```

---

## 2. Resource Boundaries & DoS Protections

| Security Boundary | Enforced Limit | Violation Outcome |
| :--- | :--- | :--- |
| **Max Single PDF File Size** | `10 MB` | `ValueError` (HTTP 400 Bad Request) |
| **Max PDF Pages Processed** | `50 pages` | Warning logged; process truncated to 50 pages |
| **Max Text Spans per Page** | `10,000 spans` | Process truncated; prevents memory exhaustion |
| **Max ZIP Archive Entries** | `50 files` | `HTTPException(400)` |
| **Max ZIP Decompression Ratio**| `100:1 ratio` | `HTTPException(400, SUSPICIOUS_ARCHIVE)` |
| **Max ZIP Uncompressed Bytes**| `50 MB` | `HTTPException(400, SUSPICIOUS_ARCHIVE)` |

---

## 3. Empirical Security Test Results (156 Tests)

```text
======================= 156 passed in 2.07s ========================
```

### Malicious Document Security Attacks Passed
* **ZipSlip Path Traversal (`../../etc/passwd`)**: `100.0% Path Canonicalized & Blocked` 🟢
* **ZIP Archive Entry Limit (>50 Files)**: `100.0% Rejected with 400 Bad Request` 🟢
* **Decompression Bomb Ratio (>100:1)**: `100.0% Rejected as SUSPICIOUS_ARCHIVE` 🟢
* **Malformed / Corrupted PDF Bytes**: `100.0% Handled safely via ValueError (0 unhandled crashes)` 🟢
* **Non-Existent Document File Path**: `100.0% Handled cleanly with FileNotFoundError` 🟢

---

## 4. Parser & OCR Limitations

1. **OCR Text Extraction**: Default extraction processes layout-aware vector text spans. Embedded scanned raster images require optional Tesseract OCR preprocessing.
2. **Encrypted PDFs**: Password-protected PDF files raise `ValueError("PDF document is encrypted/password protected.")`.

---

## 5. Phase 4 Stage 5 Status

# **`PASS`**
