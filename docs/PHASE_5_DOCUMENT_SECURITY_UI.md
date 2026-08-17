# SECUROXI AI Phase 5 Stage 6 — Document Security UI & Scan Console Specification

**Engine Version**: `0.5.0-document-security-ui`  
**Classification**: **`DOCUMENT SECURITY & SCAN CONSOLE SPECIFICATION`**  
**Stage 6 Status**: **`PASS`**  
**Date**: `2026-08-14`

---

## 1. Document Security Workflows

The **SECUROXI Scan Console** (`/scans`) provides real-time document upload, bulk ZIP archive processing, and layout-aware threat reports:

```
Upload Drag & Drop ──▶ Real API POST /api/v1/scan ──▶ Verdict & Risk Score ──▶ Forensic Evidence Viewer
```

---

## 2. Scan Console Features

1. **Drag-and-Drop & File Picker**: Supports single PDF documents and bulk ZIP archives (Max 10MB per PDF, 50MB total ZIP uncompressed limit).
2. **Real API Integration**: Uploads file via `POST /api/v1/scan` using multipart form data with real-time error handling (`Alert`).
3. **Verdict & Risk Score Cards**: Renders Verdict Badges (`SAFE`, `SUSPICIOUS`, `HIGH_RISK`, `CRITICAL`, `BLOCKED`) and risk scores (`0-100`).
4. **Forensics Evidence Viewer**: Displays exact matched prompt injection strings, line numbers, and pattern rules in monospaced security code blocks.
5. **Scan History Table**: Searchable scan history list filtering by filename or Scan ID.

---

## 3. Empirical Test Results (171 Tests)

```text
======================= 171 passed in 2.08s ========================
```
* **Real API Document Upload**: `Connected to POST /api/v1/scan & GET /scans` 🟢
* **Single & Bulk ZIP Ingestion**: `PDF & ZIP file drop active` 🟢
* **Verdict & Forensic Report View**: `Rendered with exact pattern matched text` 🟢
* **Backend API Compatibility**: `171 / 171 Backend Security Tests Passed (100%)` 🟢

---

## 4. Stage 6 Status

# **`PASS`**
