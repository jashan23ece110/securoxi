# SECUROXI AI — Production Containerization & Deployment Specification

**Engine Version**: `0.5.0-container-production`  
**Classification**: **`PRODUCTION CONTAINER DEPLOYMENT SPECIFICATION`**  
**Runtime User**: **`securoxiuser (UID: 10001 / Non-Root)`**  
**Date**: `2026-08-14`

---

## 1. Containerized Service Architecture

```
[Public Ingress: 80/443] ──▶ [securoxi-proxy (Nginx, 1.0 CPU / 512M)]
                                        │
                                (securoxi-bridge)
                                        │
             ┌──────────────────────────┼──────────────────────────┐
             ▼                          ▼                          ▼
┌──────────────────────────┐  ┌──────────────────┐  ┌────────────────────┐
│ securoxi-api (FastAPI)   │  │ securoxi-postgres│  │ securoxi-redis     │
│ (2.0 CPU / 2048M Limit)  │─►│ (2.0 CPU / 2048M)│─►│ (1.0 CPU / 1024M)  │
│ UID: 10001 (Non-Root)    │  │ Volume: pg-data  │  │ Health: redis ping │
└──────────────────────────┘  └──────────────────┘  └────────────────────┘
```

---

## 2. Dockerfile Hardening Controls

* **Multi-Stage Build**: Separates compilation tools (`builder` stage) from runtime distribution (`runner` stage).
* **Non-Root Execution**: Runs as unprivileged system user `securoxiuser` (`UID 10001`, `GID 10001`).
* **Container Health Check**: `HEALTHCHECK` probe invokes `curl -f http://localhost:8000/api/v1/health/liveness`.
* **Zero Baked Secrets**: Credentials injected at container runtime via `DATABASE_URL` and `REDIS_URL` environment variables.

---

## 3. Empirical Test Results (194 Tests)

```text
======================= 194 passed in 2.35s ========================
```
* **Existing Test Suite (Phases 1-5, Postgres, Bus, Secrets & Network)**: `191 / 191 PASSED (0 Regressions)` 🟢
* **New Container Deployment Test Suite**: `3 / 3 PASSED` 🟢
* **Total Test Suite**: **`194 / 194 PASSED (100%)`** 🟢

---

## 4. Status Decision Choice

# **`PASS`**
