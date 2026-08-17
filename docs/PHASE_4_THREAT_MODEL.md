# SECUROXI AI Phase 4 — Threat Model & Attack-Surface Audit

**Engine Version**: `0.4.0-threat-model`  
**Classification**: **`CONFIDENTIAL ENTERPRISE THREAT MODEL & AUDIT`**  
**Stage 1 Status**: **`PASS WITH LIMITATIONS`**  
**Date**: `2026-08-14`

---

## 1. System Asset Inventory & Trust Boundaries

### Key Assets
1. **Resume & JD Files**: High-value candidate PII and proprietary corporate role requirements.
2. **Security Brain & Policy Engine**: Rule definitions, risk weights, decision matrices, and correlation engines.
3. **AI Provider API Credentials**: API keys for external LLMs (e.g. Gemini API keys).
4. **Database & Audit Logs**: SQLite database storing scan reports, audit traces, and incident histories.
5. **System Execution Environment**: Python runtime, underlying OS, host filesystem, and container sandbox.

### Trust Boundaries
* **Boundary 1 (External Untrusted User / System $\rightarrow$ REST API / Webhooks)**: Ingestion of resumes, JDs, ZIP files, candidate webhooks from internet/ATS.
* **Boundary 2 (API Layer $\rightarrow$ Security Brain & Screening Engines)**: Parsing and feature extraction of untrusted file content.
* **Boundary 3 (Security Engine $\rightarrow$ External LLM / Gemini API)**: Outbound requests transmitting document snippets and receiving model responses.
* **Boundary 4 (Control Plane $\rightarrow$ System Storage / Environment)**: SQLite audit database access and environment secret resolution.

---

## 2. Threat Model Matrix & Attack-Surface Inventory

| Vulnerability ID | Vulnerability / Threat Description | Affected Component | Attack Scenario | Impact | Likelihood | Current Protection Status | Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | **Default Hardcoded API Key Fallback** | `securoxi/api/app.py` | Attacker makes REST requests without providing `X-API-Key`. Default code falls back to `securoxi-client` or `"securoxi-enterprise-key"` if `SECUROXI_API_KEY` env is unset. | Unauthorized access to scan endpoints and audit logs. | High | **PARTIALLY PROTECTED** (Authentication check exists, but weak default fallback in unconfigured environments). | **MEDIUM** |
| **SEC-02** | **Lack of Multi-Tenant Authorization Checks on Endpoints** | `securoxi/api/app.py` | An authenticated user from Tenant A queries `/api/v1/scan/{scan_id}` with a valid Scan ID belonging to Tenant B (IDOR). | Cross-tenant data leakage. | Medium | **MISSING CONTROL** (Scan query endpoints lack explicit tenant filter validation). | **HIGH** |
| **SEC-03** | **Unbounded ZIP Decompression (ZIP Bomb)** | `securoxi/api/app.py` (`process_zip_archive`) | Attacker uploads a small ZIP file expanding to 100GB of PDF data or thousands of nested files. | Denial of Service (DoS) via disk exhaustion or CPU starvation. | Medium | **PARTIALLY PROTECTED** (Path traversal checked via `ZipSlip` check, but missing uncompressed size limit). | **MEDIUM** |
| **SEC-04** | **PDF Parser Vulnerability (PyMuPDF C-library vector)** | `securoxi/parsers/pdf_parser.py` | Attacker uploads a malformed PDF triggering a buffer overflow or memory corruption bug in MuPDF C-bindings. | Potential Process Crash or Remote Code Execution (RCE). | Low | **PARTIALLY PROTECTED** (File size capped at 10MB, page count capped at 50 pages; memory isolated in sub-process). | **MEDIUM** |
| **SEC-05** | **In-Memory Event Bus Horizontal Scale Limitation** | `securoxi/brain/continuous_monitoring.py` | Continuous monitoring event bus uses Python `queue.Queue()`. High volume burst flooding overwhelms single-node memory. | Event queue overflow & processing delay. | Medium | **KNOWN LIMITATION** (Thread-safe in-memory queue; requires Redis/Kafka for multi-node clusters). | **LOW** |
| **SEC-06** | **Indirect Prompt Injection in RAG Context** | `securoxi/brain/runtime_security.py` | Untrusted vector store document containing adversarial prompts (`[SYSTEM OVERRIDE]`) fed into LLM prompt. | Manipulation of AI reasoning or candidate fit recommendation. | Medium | **FULLY PROTECTED** (`SecuroxiRuntimeSecurity` boundary inspector blocks injection and sets risk=100.0). | **LOW** |
| **SEC-07** | **Malicious Tool Argument Execution (`rm -rf /`)** | `securoxi/brain/runtime_security.py` | Attacker tricks AI agent into outputting dangerous tool call arguments targeting OS filesystem. | Destruction of system files or host corruption. | Low | **FULLY PROTECTED** (`ToolCallInspector` blocks dangerous shell args and triggers emergency `BLOCK`). | **LOW** |

---

## 3. Existing Controls vs. Missing Controls

### Existing Controls 🟢
1. **Mandatory Phase 1 Security Gate**: Every untrusted resume/JD undergoes visual deception and prompt injection scanning prior to screening or feature extraction.
2. **ZipSlip Traversal Guard**: ZIP archive extraction explicitly checks for `..` and leading `/` characters before extraction.
3. **Resource Capping**: Maximum file size strictly capped at 10MB, page limit at 50 pages, text spans at 10,000.
4. **Deterministic Policy Engine Authority**: LLM advisory recommendations cannot execute high-impact actions (`BLOCK`, `QUARANTINE`); authority is strictly enforced by priority-sorted `PolicyRule` evaluations.
5. **SHA-256 Key Hashing & XML Prompt Isolation**: Raw API keys are hashed with SHA-256; document context is safely enclosed in XML tags (`<untrusted_document_evidence>`).

### Missing Controls / Needed Enhancements 🔴
1. **Strict Multi-Tenant IDOR Guard**: Add tenant-based filter verification on `get_scan_report` (`/api/v1/scan/{scan_id}`) and `list_scans`.
2. **ZIP Uncompressed Size Ratio Limit**: Add explicit uncompressed file size byte ceiling (e.g. 50MB max uncompressed limit) in `process_zip_archive`.
3. **Mandatory Production API Key Enforcement**: Enforce non-default API key initialization when starting FastAPI in production mode (`ENVIRONMENT=production`).

---

## 4. Prioritized Remediation Backlog

1. **[PRIORITY 1 - HIGH] Multi-Tenant End-to-End Endpoint Authorization Guard**: Enforce tenant ID verification across all REST endpoints (`/api/v1/scan/{scan_id}`, `/api/v1/scans`) to prevent cross-tenant IDOR data access.
2. **[PRIORITY 2 - MEDIUM] ZIP Archive Uncompressed Size Ceiling**: Add cumulative byte decompression ratio check in `process_zip_archive` to defeat potential ZIP bomb attempts.
3. **[PRIORITY 3 - MEDIUM] Environment Production Security Enforcement**: Throw error on startup if running in production without explicit `SECUROXI_API_KEY` set.
4. **[PRIORITY 4 - LOW] Multi-Node Distributed Event Broker Adapter**: Provide Redis / Kafka event broker adapter implementation for `ContinuousEventBus`.

---

## 5. Phase 4 Stage 1 Status Decision

# **`PASS WITH LIMITATIONS`**
