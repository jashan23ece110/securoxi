# SECUROXI AI — Production Go-Live Verification Checklist

**Engine Version**: `0.5.0-go-live-checklist`  
**Classification**: **`ENTERPRISE GO-LIVE VERIFICATION CHECKLIST`**  
**Readiness Decision**: **`PRODUCTION READY WITH CONDITIONS`**  
**Date**: `2026-08-14`

---

## 1. Security & Identity Verification

* [x] **API Key Authentication**: API keys hashed via SHA-256 (`key_hash`). Plaintext secrets never committed.
* [x] **Production Secret Guard**: Startup fails safely if `ENVIRONMENT=production` and `SECUROXI_API_KEY` uses default dev key.
* [x] **RBAC Authorization**: Server-side `require_permission` checks enforce least-privilege role boundaries (`SUPER_ADMIN`, `SECURITY_ADMIN`, `RECRUITER`, `AUDITOR`).
* [x] **Multi-Tenant Isolation (IDOR Protection)**: All SQL queries explicitly filter by `tenant_id`. Cross-tenant queries return `404 Not Found`.
* [x] **Network SSRF Guard**: Outbound URLs pass through `SecuroxiSSRFGuard` blocking private subnets (`10.0.0.0/8`, `127.0.0.0/8`, `192.168.0.0/16`) and AWS IMDS (`169.254.169.254`).
* [x] **Document Security**: PyMuPDF layout-aware text span parser detects micro-text, background matching, invisible Unicode, and prompt injection. ZipSlip path canonicalization and decompression limits enforced (max 50 entries, 50MB limit, 100:1 ratio limit).
* [x] **AI Model Boundary Isolation**: Deterministic Policy Engine decision strictly overrides advisory LLM recommendations. High-impact response actions (`BLOCK`, `QUARANTINE_DOCUMENT`) remain controlled by policy rules.

---

## 2. Infrastructure & Persistence Verification

* [x] **PostgreSQL Production Persistence**: Dual-dialect `SecuroxiDatabase` abstraction supports PostgreSQL database connection strings (`DATABASE_URL`).
* [x] **Distributed Event Infrastructure**: Dual-mode `ContinuousEventBus` supports `RedisEventBus` (`redis:7-alpine`) with at-least-once delivery, retries, and Dead-Letter Queue (`securoxi:dlq`) routing.
* [x] **Container Security**: Hardened multi-stage `Dockerfile` executes as non-root user `securoxiuser` (`UID 10001`). Resource limits (CPU/Memory caps) configured in `docker-compose.yml`.
* [x] **Reverse Proxy Ingress**: Nginx ingress proxy (`docker/nginx/nginx.conf`) handles TLS 1.3/1.2 termination, HTTP $\rightarrow$ HTTPS redirect, 50MB upload size caps, and security headers (HSTS, CSP, XFO).

---

## 3. Operations & Observability Verification

* [x] **Structured JSON Logging**: Logs include `timestamp`, `service`, `severity`, `trace_id`, and `tenant_id` with automatic secret masking (`secu***`).
* [x] **Health & Readiness Probes**: `/api/v1/health/liveness` and `/api/v1/health/readiness` endpoints mounted and tested.
* [x] **SIEM Security Event Exporter**: Vendor-neutral JSON / CEF exporter (`SecuroxiSIEMExporter`) supporting Splunk, Datadog, Elastic, and Sentinel with fail-safe error isolation.
* [x] **Data Retention Cleanup**: Automated `purge_expired_data(retention_days, tenant_id)` removes scan reports and audit logs older than retention cutoff.

---

## 4. Operational Go-Live Preconditions

1. **Bind Production TLS Certificates**: Replace development SSL certificate files in `docker/nginx/ssl/` with CA-signed certificates for target live domain.
2. **Inject Vault / AWS Secrets Manager Credentials**: Populate `SECUROXI_API_KEY`, `DATABASE_URL`, and `REDIS_URL` secrets via enterprise Secrets Manager.
3. **Execute Initial Database Migration**: Run `python3 -m securoxi.storage.migrate_sqlite_to_postgres` if migrating pre-existing local SQLite scan data.

---

## 5. Final Status Decision Choice

# **`PRODUCTION READY WITH CONDITIONS`**
