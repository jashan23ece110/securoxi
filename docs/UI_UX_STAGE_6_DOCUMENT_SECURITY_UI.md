# SECUROXI AI — UI/UX Stage 6: Document Security & Scan Center Specification

**Stage**: UI/UX Stage 6 — Document Security + Scan Center  
**Status**: Verified & Operational  
**Test Baseline**: `226 / 226 PASSED` (in 2.29s)  
**Frontend Compilation**: `tsc && vite build` $\rightarrow$ `built in 780ms`  
**Route**: `/scans` (Component: [`ScansPage.tsx`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/Scans.tsx))

---

## 1. Executive Summary & Document Ingestion Philosophy

The `/scans` console is the primary ingestion and forensic inspection hub for SECUROXI. It supports single-document uploads, bulk zip ingestion, and layout-aware text/visual deception scanning across six major enterprise document formats:
* `PDF`, `DOCX`, `TXT`, `HTML`, `PNG`, and `JPG/JPEG`.

### The `UNINSPECTABLE` Security Invariant
> [!WARNING]
> **UNINSPECTABLE $\neq$ SAFE**:
> Rasterized or image-only PDF payloads that lack extractable text streams are classified as `UNINSPECTABLE`. They are **never treated as SAFE**; they are quarantined immediately and forwarded to the OCR Sandbox.

---

## 2. Ingestion & Scan Center Architecture

```
+---------------------------------------------------------------------------------------------------------------+
|  DOCUMENTS / SCAN CONSOLE                                                                                     |
|  Document Security & Multi-Format Scan Center                 [ Refresh Scans ] [ Upload Document ]          |
|  High-throughput layout parser, OCR image-quarantine pipeline & deep forensic span extraction                 |
+---------------------------------------------------------------------------------------------------------------+
|  +--------------------+ +--------------------+ +--------------------+ +------------------------------------+  |
|  | TOTAL EVALUATED    | | VERIFIED CLEAN     | | SUSPICIOUS STYLING | | OCR-QUARANTINED FILES              |  |
|  | 142                | | 120 (84.5%)        | | 18                 | | 4 (UNINSPECTABLE)                  |  |
|  | Multi-format parsed| | Passed safe        | | Concealed fonts    | | Image-only raster                  |  |
|  +--------------------+ +--------------------+ +--------------------+ +------------------------------------+  |
+---------------------------------------------------------------------------------------------------------------+
|  [ INGEST PAYLOAD FOR ON-DEMAND FORENSIC ANALYSIS ]                                                           |
|  + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +  |
|  |   [ (^) ] Drag & Drop file payload here, or browse local workspace                                      |  |
|  |   Max: 25MB/doc • Formats: [PDF] [DOCX] [TXT] [HTML] [PNG] [JPG/JPEG] [ZIP]                             |  |
|  + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +  |
|  Selected: alex_resume.pdf (142.5 KB)                                        [ Execute Threat Scan (Zap) ]    |
+---------------------------------------------------------------------------------------------------------------+
|  Search: [Filter scans...]   Format: [All Formats v]   Verdict: [All Verdicts v]   Showing 142 of 142 records |
|  -----------------------------------------------------------------------------------------------------------  |
|  Scan ID   | Document Name           | Format | Verdict          | Risk Score | Findings | Actions        |
|  SC-901    | alex_resume.pdf         | PDF    | [BLOCKED]        | [====] 95  | 2        | [ Inspect ]    |
|  SC-902    | elena_rostova_cv.docx   | DOCX   | [ SAFE ]         | [=   ] 12  | 0        | [ Inspect ]    |
|  SC-903    | scanned_receipt.png     | PNG    | [UNINSPECTABLE]  | [=== ] 65  | 1        | [ Inspect ]    |
+---------------------------------------------------------------------------------------------------------------+
```

---

## 3. Deep Forensic Drawer Capabilities

Clicking **"Inspect"** on any document scan opens the sliding forensic drawer ([`Drawer.tsx`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/components/ui/Drawer.tsx)), presenting:
1. **`UNINSPECTABLE` Warning Banner**:
   * Explicitly alerts the analyst if the file is an uninspectable raster image quarantined for OCR sandboxing.
2. **Calibrated Document Risk Gauge**:
   * 0–100 numerical risk score with dynamic threshold color mapping.
3. **Format & Metadata Tags**:
   * File format, file size, ingestion timestamp, and scan ID.
4. **Extracted Forensic Spans (`EvidenceBlock`)**:
   * Exact matched payload in monospace codeblock with one-click copy.
   * Span coordinates (`Layout Span [72.0, 140.5, 540.0, 148.0]` or Line numbers).
   * Detector engine provenance (`PromptInjectionDetector`, `VisualDeceptionDetector`, `OcrSecurityEngine`).
   * Confidence metrics and root-cause rationale.

---

## 4. Verification & Quality Assurance

* **TypeScript & Vite Build**: `✓ built in 780ms` (0 errors).
* **Backend Pytest Suite**: `226 passed, 5 warnings in 2.29s` (100% pass rate).
* **Multi-Format Ingestion**: Validated against `PDF`, `DOCX`, `TXT`, `HTML`, `PNG`, and `JPG/JPEG` payloads.
