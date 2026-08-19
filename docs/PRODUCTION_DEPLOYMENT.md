# SECUROXI AI — Production Deployment Architecture & Guide (Stage 25)

**Version**: v2.0.0-production-hardened  
**Baseline Test Suite**: **`479 / 479 PASSED`** (7 new Production Readiness tests + 472 existing regression tests)  
**Status**: **PRODUCTION HARDENED & ACTIVE** 🟢  

---

## 1. Production Architecture Overview

The SECUROXI AI system follows a multi-tenant, zero-trust architecture designed for containerized cloud and on-premises deployments:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        INTERNET / CLIENTS                              │
│         HTTPS (TLS 1.3) • WAF • Rate Limiting (120 req/min)            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     SECUROXI API SERVER (FastAPI)                      │
│  • Non-root container runtime (securoxiuser:10001)                     │
│  • Role-Based Access Control (RBAC) & Multi-Tenant Context             │
│  • Liveness (/api/v1/health/liveness) & Readiness Probes               │
├────────────────────────────────────────────────────────────────────────┤
│  • Agent Orchestrator & Task Execution Runner                          │
│  • SecuroxiScanner & Visual Deception Engine                           │
│  • Hybrid Retrieval + Reranking + Groundedness Verifier                │
│  • Human Approval & Governance Gate                                    │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
                    ▼                                ▼
┌──────────────────────────────────────┐  ┌──────────────────────────────┐
│       PERSISTENT STORAGE / DB        │  │     EXTERNAL PROVIDERS       │
│  • PostgreSQL 16 (or WAL SQLite)     │  │  • Gemini 2.5 Flash / Models │
│  • Encrypted Volume (/app/data)      │  │  • ATS Webhook Integrations  │
│  • Immutable Audit Logs              │  │  • Monitoring / Telemetry    │
└──────────────────────────────────────┘  └──────────────────────────────┘
```

---

## 2. Environment Configuration Matrix

| Variable | Environment | Default / Example | Purpose |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | All | `production` / `staging` / `development` | Active deployment profile |
| `SECUROXI_API_KEY` | Production | *[Secret Value]* | Master enterprise authorization key |
| `DATABASE_URL` | Production | `postgresql://user:pass@host:5432/securoxi` | Relational storage connection |
| `STORAGE_ROOT` | Production | `/app/data/storage` | Document and evidence cache root |
| `CORS_ALLOWED_ORIGINS`| Production | `https://app.securoxi.ai` | Strictly allowlisted origins |
| `AI_PROVIDER` | Production | `gemini` (or `mock` for airgap) | Security reasoning provider |
| `GEMINI_API_KEY` | Production | *[Secret Value]* | API key for Gemini inference |

---

## 3. Container Deployment (Docker Compose)

### Development / Staging:
```bash
docker compose up -d --build
```

### Production:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

---

## 4. Health & Monitoring Probes

- **Liveness Probe**: `GET http://localhost:8000/api/v1/health/liveness` $\to$ Returns `{"status": "alive"}`
- **Readiness Probe**: `GET http://localhost:8000/api/v1/health/readiness` $\to$ Verifies DB connection and returns `{"status": "ready"}`
