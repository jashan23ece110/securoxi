# SECUROXI AI — Complete Product Architecture Specification

**Engine Version**: `0.5.0-final-architecture`  
**Classification**: **`FINAL END-TO-END PRODUCT ARCHITECTURE`**  
**Audit Status**: **`VERIFIED AGAINST READ-ONLY CODEBASE`**  
**Date**: `2026-08-14`

---

## 1. End-to-End System Architecture

```
[Enterprise Client / Web SPA]
       │
  (HTTPS REST API Calls + API Key Header)
       │
       ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   SECUROXI FASTAPI API & INGRESS GATE                   │
│                                                                        │
│  - Middleware: Secure HTTP Headers (nosniff, DENY, HSTS)               │
│  - Network Security: SecuroxiSSRFGuard (Blocks 127.0.0.1, 10.0.0.0/8,  │
│                       192.168.0.0/16, AWS IMDS 169.254.169.254)         │
│  - Identity Auth: SHA-256 Key Hash + Production Key Enforcement        │
│  - RBAC Guard: Server-side require_permission(SUPER_ADMIN, RECRUITER) │
│  - Multi-Tenant Gate: Strict WHERE tenant_id = ? IDOR Containment      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   DOCUMENT SECURITY ENGINE (PHASE 1)                   │
│                                                                        │
│  - PyMuPDF Parser: Layout-aware text span extraction                   │
│  - DoS Safeguards: Max 10MB file, 50 pages, 50 ZIP entries, 100:1 ratio│
│  - Threat Inspectors: Prompt Injection, Micro-text, Background match,  │
│                        Invisible Unicode, Visual Deception             │
│  - Evidence Engine: Bounding boxes, line numbers, matched text snippets │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  SECURITY-AWARE SCREENING ENGINE (PHASE 2)             │
│                                                                        │
│  - Security Gate: High-risk resumes quarantined at Rank #0 (Score 0.0)│
│  - Extractor: Structured candidate profile & skill normalization       │
│  - Semantic Matcher: Embeddings cosine similarity fit scoring (0-100)  │
│  - Report Generator: Explainable qualification breakdown & evidence    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   ENTERPRISE SECURITY BRAIN (PHASE 3)                  │
│                                                                        │
│  - Correlation Pipeline: Signal -> Forensics -> Detection -> Graph     │
│  - Attack Graph: Node-edge threat actor & artifact relationships       │
│  - Runtime AI Inspector: Input, RAG Context, Tool Call & Output guard  │
│  - Tool Security: Block shell_exec, rm -rf /, sudo, chmod 777          │
│  - Policy Engine: Deterministic Rule Priority (Policy OVERRIDES LLM)   │
│  - Incident Manager: Lifecycles, severity triage, assignment           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   DATA PERSISTENCE & INTEGRATIONS (PHASE 4)            │
│                                                                        │
│  - Database: SecuroxiDatabase (SQLite default with PostgreSQL driver)  │
│  - Retention Engine: purge_expired_data(retention_days, tenant_id)     │
│  - Audit Engine: Immutable multi-tenant audit logs                     │
│  - Connectors: Greenhouse, Lever, Local Files, ZIP, Cloud Storage      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Subsystem Components & Responsibilities

### A. Frontend Layer (`frontend/`)
* **Technology**: React 18 + TypeScript 5.2 + Vite 5.1 + Custom CSS Tokens.
* **Routing**: Client-side React Router DOM v6 serving 11 enterprise routes (`/overview`, `/security-brain`, `/incidents`, `/scans`, `/screening`, `/ats`, `/monitoring`, `/policies`, `/audit`, `/settings`, `/design-system`).
* **API Client**: `SecuroxiApiClient` consuming FastAPI REST endpoints with error boundary handling.

### B. Network & API Ingress Layer (`securoxi/network_security.py` & `securoxi/api/app.py`)
* **SSRF Guard**: `SecuroxiSSRFGuard` validates outbound URLs, resolving DNS and blocking private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`) and AWS Metadata IMDS (`169.254.169.254`).
* **Identity & RBAC**: API keys stored as SHA-256 hashes (`key_hash`). Server-side `require_permission` checks ensure zero privilege escalation.
* **Multi-Tenant Isolation**: Database queries explicitly filter by `tenant_id`. Cross-tenant IDOR attempts yield `404 Not Found`.

### C. Security Brain & Policy Engine (`securoxi/brain/`)
* **7-Stage Correlation Pipeline**: Signal → Forensics → Detection → Context → Correlation → Attack Graph → Policy.
* **Deterministic Policy Engine**: Policy rule priority registry (`RULE-100-HIGH-RISK-BLOCK`, `RULE-090-PROMPT-INJECTION-QUARANTINE`). Enforces `BLOCK` or `QUARANTINE_DOCUMENT` regardless of LLM advice (`Policy OVERRIDES LLM`).

### D. Data Persistence & Retention (`securoxi/storage/db.py`)
* **Database Driver**: `SecuroxiDatabase` providing SQLite table schema with dynamic `PRAGMA table_info` migrations and abstract PostgreSQL connection compatibility.
* **Data Lifecycle**: `purge_expired_data(retention_days, tenant_id)` removes scan reports and audit logs older than retention cutoff.

---

## 3. Architecture Status

# **`VERIFIED & FROZEN`**
