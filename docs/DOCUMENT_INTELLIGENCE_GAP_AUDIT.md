# SECUROXI AI — Document Intelligence & Processing Architectural Gap Audit

**Audit Version**: `1.0.0-gap-audit`  
**Classification**: **`ARCHITECTURAL GAP AUDIT REPORT`**  
**Audit Scope**: **Document Ingestion, Parsers, OCR, Chunking, Vector Search, RAG & Scale**  
**Date**: `2026-08-15`  
**Workspace**: `/Users/jashanpreetsingh/Downloads/SECUROXI`

---

## 1. File Type Audit

| File Format / Feature | Current Status | Code Evidence | Operational Behavior & Handling |
| :--- | :--- | :--- | :--- |
| **PDF Documents** | **`SUPPORTED`** | `securoxi/parsers/pdf_parser.py` (Line 45) | Layout-aware parsing via PyMuPDF (`fitz`). Extracts spans, font size, hex color, bbox. |
| **DOCX Documents** | **`NOT SUPPORTED`** | `securoxi/engine.py` (Lines 87–96) | No `DocxParser` exists. Registered parsers list only contains `.pdf`. Returns `UNSUPPORTED_FORMAT`. |
| **TXT Files** | **`PARTIALLY SUPPORTED`** | `securoxi/screening/ingestion.py` (Line 112) | Supported for Job Description text input. **`NOT SUPPORTED`** in core Security Engine `scan()`. |
| **HTML Files** | **`NOT SUPPORTED`** | `securoxi/engine.py` (Lines 87–96) | No HTML parser registered. Returns `UNSUPPORTED_FORMAT`. |
| **Images (PNG, JPG, TIFF)**| **`NOT SUPPORTED`** | `securoxi/engine.py` (Lines 87–96) | No image parser registered. Returns `UNSUPPORTED_FORMAT`. |
| **Scanned / Image PDFs** | **`PARTIALLY SUPPORTED / FAILED`** | `securoxi/parsers/pdf_parser.py` (Lines 89–94) | PyMuPDF opens PDF successfully, but `get_text("dict")` yields 0 text spans (`len(spans) == 0`). |
| **ZIP Archives** | **`SUPPORTED`** | `securoxi/api/app.py` & `SecuroxiScanner` | Extracts entries sequentially into temporary workspace. Enforces max 50 entries and ZipSlip protection. |
| **Nested ZIP Archives** | **`NOT SUPPORTED`** | `securoxi/api/app.py` | Single flat iteration over ZIP entries; nested sub-ZIP files are flagged as unparseable files. |
| **Corrupted Files** | **`SUPPORTED`** | `securoxi/engine.py` (Lines 103–111) | Catches `fitz.open()` exception, returns `SUSPICIOUS` report with `PARSER_FAILURE` error code. |
| **Empty Files (0 Bytes)** | **`SUPPORTED`** | `securoxi/screening/ingestion.py` (Line 50) | Validates `file_size == 0`, raises `ValueError("Resume document is empty (0 bytes).")`. |
| **Password-Protected PDFs**| **`SUPPORTED`** | `securoxi/parsers/pdf_parser.py` (Lines 74–77) | Checks `doc.is_encrypted`, raises `ValueError("PDF document is encrypted/password protected.")`. |
| **Encrypted Archives** | **`SUPPORTED`** | `securoxi/api/app.py` | Catches `zipfile.BadZipFile` / RuntimeError, returns `SUSPICIOUS` report. |

---

## 2. Extraction Audit

### PDF Attribute Extraction Capabilities (`securoxi/parsers/pdf_parser.py`)
* **Text Content**: `EXTRACTED` (`span.get("text")`).
* **Font Size**: `EXTRACTED` (`round(span.get("size"), 2)`).
* **Font Color**: `EXTRACTED` (Converted from 24-bit sRGB integer to `#RRGGBB` hex string).
* **Bounding Box Coordinates**: `EXTRACTED` (`[x0, y0, x1, y1]` in page canvas pixel units).
* **Page Number**: `EXTRACTED` (`page_num + 1`).
* **Font Family / Name**: `EXTRACTED` (`span.get("font")`).
* **Hidden / Offscreen Flags**: `EXTRACTED` (Checks rendering flags `flags & 1` and offscreen coordinates).
* **Background Color**: **`NOT EXTRACTED`** (Hardcoded to canvas default `#FFFFFF` in line 140; actual underlying vector rectangle fill colors are NOT extracted from PDF streams).

### Metadata Loss During Screening Normalization (`securoxi/screening/ingestion.py`)
When converting PDF text spans into raw resume text (`raw_text = "\n".join(s.text for s in spans)`), **all layout coordinates, font sizes, text colors, page numbers, and visual hierarchy attributes are completely lost**, leaving only unformatted text strings.

---

## 3. OCR (Optical Character Recognition) Audit

* **Is OCR currently implemented?**: **`NO`** (`pytesseract`, `easyocr`, `tesseract`, `paddleocr` are completely absent from the codebase).
* **Is OCR triggered automatically?**: **`NO`**.
* **Scanned / Image-Only PDF Behavior**:
  1. PyMuPDF opens the PDF file without raising an exception.
  2. `doc.get_text("dict")` returns zero text blocks $\rightarrow$ `len(spans) == 0`.
  3. Visual deception and prompt injection analyzers receive 0 text spans $\rightarrow$ detect 0 findings.
  4. `SecuroxiRiskEngine.evaluate()` evaluates 0 findings and returns **`Verdict.SAFE` with Risk Score `0`**!
  * **CRITICAL SECURITY RISK**: An image-only PDF containing printed prompt injection or visual deception attacks yields zero text spans and is currently reported as **`SAFE` (Risk Score 0)** because the engine cannot inspect its contents.

---

## 4. Blank & Empty Document Audit

| Document Type | Ingestion Result | Security Verdict | Vulnerability Assessment |
| :--- | :--- | :--- | :--- |
| **Completely Empty PDF (0 Bytes)** | `ValueError` raised in `ingestion.py` | `SUSPICIOUS` (Score 40) | Safe failure (`PARSER_FAILURE`). |
| **Scanned PDF (Image Only)** | PyMuPDF yields 0 spans | **`SAFE` (Score 0)** | **CRITICAL VULNERABILITY**: System fails to distinguish `CONTENT_ANALYZED` from `CONTENT_NOT_ANALYZABLE`. |
| **PDF with Minimal Text (1-2 Words)**| Parsed over 1-2 words | `SAFE` (Score 0) | Analyzed normally over extracted text. |
| **Empty DOCX / Image File** | Unsupported format error | `SUSPICIOUS` (Score 40) | Handled safely via format check. |

---

## 5. Large Document & Capacity Audit

### Configured Resource Boundaries (`securoxi/config.py`)
* `max_file_size_bytes`: `10,485,760` bytes (10 MB per file)
* `max_pdf_pages`: `100` pages per document
* `max_spans_per_doc`: `50,000` text spans per document
* `max_zip_entries`: `50` entries per ZIP archive
* `max_total_uncompressed_bytes`: `52,428,800` bytes (50 MB total uncompressed)
* `max_compression_ratio`: `100.0` (Zip Bomb safeguard)

### Processing Scale Evaluation
* **1 Resume**: Processed in `~1.2s` (`~15MB` RAM usage).
* **100 Resumes**: Processed sequentially in `~120s` (2 minutes).
* **500 Resumes**: Processed sequentially in `~10 minutes` (single HTTP request timeout risk).
* **1,000 Resumes**: Exceeds `max_zip_entries` limit (50 entries max per archive). Requires 20 separate bulk ZIP uploads.
* **5,000 Resumes**: Cannot be processed in single-node synchronous mode. Exceeds process memory and request timeout limits.

---

## 6. Bulk Processing Architecture Audit

* **Current Flow**: ZIP Upload $\rightarrow$ Temporary Extraction Directory $\rightarrow$ Path Traversal Check $\rightarrow$ Sequential `for` Loop over Files $\rightarrow$ `SecuroxiEngine.analyze_document()` $\rightarrow$ JSON Array Response.
* **Architecture Classification**: **`SINGLE-NODE BULK PROCESSING`**.
  * Concurrency: Single-threaded sequential execution within FastAPI process.
  * Process Restart Survival: In-memory loop state lost if process restarts during bulk upload.
  * Multi-Node Distribution: **`NOT IMPLEMENTED`**.
  * Retry & Partial Failure Handling: Catches per-file parsing exceptions and returns error report without crashing the batch.

---

## 7. Document Chunking Audit

* **Status**: **`NOT IMPLEMENTED`**.
* Document text is passed as a single unchunked string (`raw_text`) or flat array of layout spans (`spans`). No fixed-size, sliding window, section-boundary, or semantic chunking exists in the ingestion pipeline.

---

## 8. Embeddings & Vector Database Audit

* **Status**: **`NOT IMPLEMENTED`**.
* The codebase contains **zero** embedding models (OpenAI embeddings, SentenceTransformers, HuggingFace).
* The codebase contains **zero** vector databases or indices (pgvector, Qdrant, Weaviate, Pinecone, FAISS, Chroma, Milvus, Elasticsearch).
* Candidate-to-JD qualification matching uses keyword regex extraction and prompt string interpolation in `securoxi/screening/matching_engine.py` and `securoxi/screening/qualification_analyzer.py`.

---

## 9. RAG (Retrieval-Augmented Generation) Audit

* **Status**: **`RAG NOT IMPLEMENTED`**.
* The application passes full raw resume text directly into LLM prompts (`document_text_context` in `securoxi/reasoning/service.py`). No vector retrieval or context assembly occurs.
* *Note*: `securoxi/brain/runtime_security.py` includes a helper method `inspect_rag_context(context_chunks)` to evaluate *external* RAG context chunks if supplied by a caller, but SECUROXI *itself* has no internal RAG retrieval pipeline.

---

## 10. Document Intelligence Pipeline Audit

| Pipeline Stage | Implemented Status | Architectural Details & Limitations |
| :--- | :--- | :--- |
| **1. INPUT** | `IMPLEMENTED` | File path validation, size caps, extension checks. |
| **2. VALIDATION** | `IMPLEMENTED` | File size (10MB), page limit (100), ZipBomb ratio check (100:1). |
| **3. PARSING** | `PARTIAL` | PyMuPDF PDF parser implemented; DOCX, TXT, HTML missing. |
| **4. OCR** | `MISSING` | No OCR engine for scanned PDFs or image documents. |
| **5. NORMALIZATION**| `IMPLEMENTED` | Lowercasing, whitespace normalization, span aggregation. |
| **6. STRUCTURE EXTRACTION**| `PARTIAL` | Keyword-based section partitioning (`SUMMARY`, `EXPERIENCE`, `EDUCATION`, `SKILLS`). |
| **7. CHUNKING** | `MISSING` | No document chunking mechanism. |
| **8. INDEXING** | `MISSING` | No vector index or full-text search index. |
| **9. SECURITY ANALYSIS**| `IMPLEMENTED` | Layout-aware visual deception and regex prompt injection analyzers. |
| **10. SCREENING** | `IMPLEMENTED` | Security clearance gate + semantic requirement matching. |
| **11. STORAGE** | `IMPLEMENTED` | Dual SQLite/PostgreSQL persistence. |

---

## 11. Final Gap Matrix

| Capability | Current Status | Code Evidence | Enterprise Requirement | Gap Classification |
| :--- | :--- | :--- | :--- | :--- |
| **PDF Extraction** | `IMPLEMENTED` | `securoxi/parsers/pdf_parser.py` | Extract PDF text & visual attributes | **NO GAP** 🟢 |
| **DOCX Extraction** | `MISSING` | `securoxi/engine.py` (Line 87) | Ingest enterprise Word resumes | **HIGH GAP** 🔴 |
| **OCR Capability** | `MISSING` | `securoxi/parsers/` | Extract text from scanned/image PDFs | **CRITICAL GAP** 🔴 |
| **Empty/Scanned Handling**| `PARTIAL` | `securoxi/engine.py` (Line 137) | Flag uninspectable docs as `UNINSPECTABLE` | **CRITICAL GAP** 🔴 |
| **Bulk Processing** | `PARTIAL` | `securoxi/api/app.py` | Process 5,000+ files concurrently | **HIGH GAP** 🔴 |
| **Document Chunking** | `MISSING` | `securoxi/screening/ingestion.py` | Chunk documents for precise reasoning | **MEDIUM GAP** 🟡 |
| **Embeddings** | `MISSING` | `securoxi/screening/` | Semantic vector representations | **HIGH GAP** 🔴 |
| **Vector DB** | `MISSING` | `securoxi/storage/` | Scalable similarity search & RAG | **HIGH GAP** 🔴 |
| **Retrieval Engine** | `MISSING` | `securoxi/screening/` | Retrieve relevant resume sections | **HIGH GAP** 🔴 |
| **RAG Pipeline** | `MISSING` | `securoxi/reasoning/` | Document-grounded LLM analysis | **MEDIUM GAP** 🟡 |
| **Distributed Scaling** | `MISSING` | `securoxi/brain/continuous_monitoring.py` | Multi-worker distributed task processing | **HIGH GAP** 🔴 |
| **Failure Recovery** | `IMPLEMENTED` | `securoxi/engine.py` (Line 166) | Safe exception catching & error report | **NO GAP** 🟢 |

---

## 12. Architectural Recommendations & Next Steps

### 1. What SECUROXI Can Process TODAY
* Text-based PDF documents up to 100 pages / 10MB.
* ZIP archives containing up to 50 text-based PDF files.
* Single-node synchronous security scanning & candidate screening.

### 2. What SECUROXI Cannot Process TODAY
* DOCX, TXT, HTML, PNG, JPG, or TIFF documents.
* Scanned or image-only PDF documents (yields 0 text spans).
* Bulk archives with >50 files or nested sub-ZIP archives.
* Distributed parallel processing across multiple worker nodes.

### 3. Critical Ingestion Weaknesses & Risks
* **Uninspectable Document Security Blind Spot**: Scanned PDFs with 0 text spans are currently assigned **`Verdict.SAFE` (Risk Score 0)** because no findings are detected. SECUROXI must introduce an explicit **`CONTENT_NOT_ANALYZABLE` / `UNINSPECTABLE`** verdict state to prevent uninspectable documents from bypassing security.
* **Format Limitation**: Enterprise HR pipelines heavily use `.docx` files. Restricting resume screening to `.pdf` limits real-world enterprise adoption.

### 4. Subsystem RAG & Retrieval Recommendations
* **Phase 1 Security Scanning**: `No RAG Required`. (Security scanning requires deterministic visual span layout analysis).
* **Phase 2 Resume-to-JD Screening**: `Hybrid Retrieval + Vector Search Recommended` for candidate pools >1,000 resumes.
* **Security Brain**: `Vector Indexing Recommended` for cross-tenant threat correlation and incident search.

---

## 13. Status Decision Choice

# **`ARCHITECTURAL AUDIT COMPLETE`**
