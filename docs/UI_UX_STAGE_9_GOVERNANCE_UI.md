# SECUROXI AI — UI/UX Stage 9: Enterprise Governance Experience Specification

**Stage**: UI/UX Stage 9 — Enterprise Governance Experience  
**Status**: Verified & Operational  
**Test Baseline**: `226 / 226 PASSED` (in 2.32s)  
**Frontend Compilation**: `tsc && vite build` $\rightarrow$ `built in 826ms`  
**Routes Covered**:
* `/ats` ([`ATSPage.tsx`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/ATS.tsx))
* `/policies` ([`PoliciesPage.tsx`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/Policies.tsx))
* `/audit` ([`AuditPage.tsx`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/Audit.tsx))
* `/settings` ([`SettingsPage.tsx`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/Settings.tsx))

---

## 1. Executive Summary & Governance Overview

Stage 9 delivers a cohesive, enterprise-grade governance and administrative control plane. It spans four critical pillars:
1. **ATS Ingress Connectors** (`/ats`): Live webhook health, provider environment tiers (`PRODUCTION`, `CONFIGURED`, `STAGING`, `MOCK`), and payload ingestion metrics.
2. **Deterministic Policy Engine** (`/policies`): Priority-ordered mitigation rules (P-100 down to P-10) with custom policy creation.
3. **Immutable Multi-Tenant Audit Trail** (`/audit`): Verifiable HMAC-signed event records with JSON export.
4. **Settings & Security Governance** (`/settings`): RBAC least-privilege matrix, one-time secret API key generation, SSRF guardrails, and data retention lifecycles.

---

## 2. Governance Architecture

```
+---------------------------------------------------------------------------------------------------------------+
|  ENTERPRISE GOVERNANCE DOMAIN                                                                                 |
+---------------------------------------------------------------------------------------------------------------+
|  1. ATS INGRESS CONNECTORS (/ats)                                                                             |
|  - Providers: Greenhouse (Prod), Lever (Configured), Workday (Staging), Sandbox (Mock)                        |
|  - Webhook status, HMAC verification, payload counts, sync test actions                                       |
+---------------------------------------------------------------------------------------------------------------+
|  2. DETERMINISTIC POLICY ENGINE (/policies)                                                                   |
|  - Priority Ranks: P-100 (Block >=80), P-90 (Prompt Injection Quarantine), P-70 (OCR Quarantine), P-10 (Allow)|
|  - Rule condition evaluation, modal rule creator, and enforcement trigger counts                              |
+---------------------------------------------------------------------------------------------------------------+
|  3. IMMUTABLE MULTI-TENANT AUDIT TRAIL (/audit)                                                               |
|  - Verifiable event explorer with signed HMAC-SHA256 signatures                                               |
|  - Filter by action type, principal actor, date range, and exportable JSON stream                             |
+---------------------------------------------------------------------------------------------------------------+
|  4. CONTROL PLANE & SECURITY GOVERNANCE (/settings)                                                           |
|  - API Key provisioning with strict ONE-TIME SECRET REVEAL workflow                                           |
|  - RBAC Matrix (SuperAdmin, SecurityAdmin, Recruiter, Auditor)                                                |
|  - SSRF Outbound Guard, PostgreSQL Row-Level Security, and Automated Data Retention Purging                  |
+---------------------------------------------------------------------------------------------------------------+
```

---

## 3. Key Capabilities Delivered

### 3.1 ATS Connectors (`/ats`)
* Delineates between live `PRODUCTION` webhooks (Greenhouse) and `MOCK` sandboxes.
* Validates SHA-256 HMAC signatures on all inbound webhook requests.
* Provides "Sync Now" test triggers and deep configuration inspection drawer.

### 3.2 Deterministic Policy Governance (`/policies`)
* Visual priority tags (`P-100` down to `P-10`) representing sequential evaluation order.
* Interactive policy creation modal with custom conditions and actions (`BLOCK`, `QUARANTINE_DOCUMENT`, `REVIEW`, `ALLOW`).
* Inspection drawer displaying exact condition strings and historic trigger counts.

### 3.3 Verifiable Audit Trail (`/audit`)
* Cryptographically signed HMAC-SHA256 audit log records.
* Real-time search across event types, tenant IDs, and principal actors.
* One-click JSON export for external SIEM integration and compliance reporting.

### 3.4 Control Plane & API Key Provisioning (`/settings`)
* **One-Time Secret Reveal Workflow**: Secrets are hashed with SHA-256 before persistence and displayed only once upon generation.
* **RBAC Matrix**: Enforces strict backend permission boundaries for SuperAdmin, SecurityAdmin, Recruiter, and Auditor.
* **Security Guardrails**: Toggleable SSRF outbound protections and automated data retention purging.

---

## 4. Verification Results

* **TypeScript & Vite Build**: `✓ built in 826ms` (0 errors).
* **Backend Pytest Suite**: `226 passed, 5 warnings in 2.32s` (100% pass rate).
* **Security & Secret Integrity**: Raw API secrets are never persisted in plaintext.
