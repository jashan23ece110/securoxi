# SECUROXI AI — Document Intelligence Stage 4: Structure Extraction & Semantic Chunking Specification

**Engine Version**: `0.6.0-doc-intel-chunking`  
**Classification**: **`DOCUMENT STRUCTURE & CHUNKING SPECIFICATION`**  
**Chunking Strategies**: **`SECTION, PARAGRAPH, FIXED_TOKEN, HYBRID_SEMANTIC`**  
**Date**: `2026-08-15`

---

## 1. Dual Document Architecture Topology

To satisfy both forensic security scanning and large-scale semantic retrieval, SECUROXI AI maintains a **Dual Document Representation**:

```
                              [Input Document]
                                      │
                     (Unified Multi-Format Extraction)
                                      │
       ┌──────────────────────────────┴──────────────────────────────┐
       ▼                                                             ▼
[FORENSIC DOCUMENT]                                        [SEMANTIC DOCUMENT]
- Spans (`TextSpan` Array)                                 - Sections (`DocumentSection`)
- Font Size & sRGB Hex Color                               - Chunks (`DocumentChunk`)
- Bounding Box Pixel Coordinates `[x0,y0,x1,y1]`            - Token & Character Counts
- Visual Deception Flags & Hidden Text                     - Layout Provenance & Page Bounds
- Used by Phase 1 Security Scanning Engine                 - Used by Phase 2 Screening & RAG Retrieval
```

---

## 2. Document Chunk Schema (`DocumentChunk`)

```json
{
  "chunk_id": "CHUNK-a1b2c3d4",
  "document_id": "RES-89123",
  "tenant_id": "TENANT-ALPHA",
  "section_heading": "WORK EXPERIENCE",
  "text": "Principal Engineer at TechCorp (2020 - Present). Built distributed event pipelines.",
  "start_page": 1,
  "end_page": 1,
  "bbox": [50.0, 155.0, 500.0, 175.0],
  "token_count": 18,
  "char_count": 83,
  "security_status": "SAFE",
  "source_spans_count": 1,
  "metadata": {
    "sources": ["NATIVE_PDF"],
    "has_hidden_spans": false
  }
}
```

---

## 3. Chunking Strategies & Performance Benchmarks

* **`SECTION`**: Segments text by structural headings (`SUMMARY`, `EXPERIENCE`, `EDUCATION`, `SKILLS`).
* **`PARAGRAPH`**: Segments by paragraph breaks and character counts (`~400 chars`).
* **`FIXED_TOKEN`**: Fixed-size windowing (`max_chunk_tokens=512`, `overlap_tokens=64`).
* **`HYBRID_SEMANTIC`**: Section-aware chunking with sub-chunking for oversized sections.
* **Chunking Latency**: **`< 0.5ms`** per document (100% deterministic, 0 LLM API calls).

---

## 4. Empirical Test Results (212 Tests)

```text
======================= 212 passed in 2.30s ========================
```
* **Existing Test Suite (Phases 1-5, Infrastructure, Stage 1 & 2)**: `208 / 208 PASSED (0 Regressions)` 🟢
* **New Stage 4 Chunking Test Suite**: `4 / 4 PASSED` 🟢
* **Total Test Suite**: **`208 + 4 = 212 / 212 PASSED (100%)`** 🟢

---

## 5. Status Decision Choice

# **`PASS`**
