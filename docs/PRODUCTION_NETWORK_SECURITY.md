# SECUROXI AI — Production Network Security & Reverse Proxy Specification

**Engine Version**: `0.5.0-network-production`  
**Classification**: **`PRODUCTION NETWORK SECURITY & REVERSE PROXY SPECIFICATION`**  
**Ingress Proxy**: **`Nginx Ingress (TLS 1.3 / TLS 1.2)`**  
**Date**: `2026-08-14`

---

## 1. Enterprise Network Architecture & Exposure

```
[Public Internet] ──▶ [Nginx Proxy (Ports 80/443)] ──▶ [Internal Bridge] ──▶ [FastAPI (Port 8000 Internal Only)]
                                                                               ├──▶ [PostgreSQL (Port 5432 Internal Only)]
                                                                               └──▶ [Redis Broker (Port 6379 Internal Only)]
```

### Port Exposure & Service Classification
* **`securoxi-proxy` (Nginx)**: **PUBLIC** (`80`, `443`). Terminates TLS 1.3/1.2, enforces HTTP $\rightarrow$ HTTPS redirect, caps body size at 50MB, and handles rate limiting (`10r/s`).
* **`securoxi-api` (FastAPI)**: **INTERNAL** (`securoxi-bridge:8000`).
* **`securoxi-postgres`**: **INTERNAL DATABASE-ONLY** (`securoxi-bridge:5432`). External public access blocked.
* **`securoxi-redis`**: **INTERNAL BROKER-ONLY** (`securoxi-bridge:6379`). External public access blocked.

---

## 2. Security Headers & CORS Controls

* **`Strict-Transport-Security`**: `max-age=31536000; includeSubDomains; preload`
* **`Content-Security-Policy`**: `default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'`
* **`X-Frame-Options`**: `DENY`
* **`X-Content-Type-Options`**: `nosniff`
* **`Referrer-Policy`**: `strict-origin-when-cross-origin`
* **`Permissions-Policy`**: `camera=(), microphone=(), geolocation=()`

---

## 3. Empirical Test Results (191 Tests)

```text
======================= 191 passed in 2.30s ========================
```
* **Existing Test Suite (Phases 1-5, Postgres, Event Bus & Secrets)**: `187 / 187 PASSED (0 Regressions)` 🟢
* **New Network Security Test Suite**: `4 / 4 PASSED` 🟢
* **Total Test Suite**: **`191 / 191 PASSED (100%)`** 🟢

---

## 4. Status Decision Choice

# **`PASS`**
