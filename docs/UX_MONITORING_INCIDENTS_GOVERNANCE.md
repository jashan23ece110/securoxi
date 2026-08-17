# SECUROXI AI — Monitoring, Incidents & Enterprise Governance Experience

**Module**: Enterprise Operations, Incident Response & Governance  
**Pages**: [`MonitoringPage.tsx`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/Monitoring.tsx), [`IncidentsPage.tsx`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/Incidents.tsx), [`PoliciesPage.tsx`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/Policies.tsx), [`AuditPage.tsx`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/Audit.tsx), [`SettingsPage.tsx`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/frontend/src/pages/Settings.tsx)  
**Backend Endpoints**: `GET /api/v1/health/liveness`, `GET /api/v1/health/readiness`, `GET /api/v1/incidents`, `GET /api/v1/audit/logs`  
**Routes**: `/monitoring`, `/incidents`, `/policies`, `/audit`, `/settings`  
**Test Baseline**: `253 / 253 PASSED` (in 3.39s)  
**Frontend Compilation**: `tsc && vite build` $\rightarrow$ `✓ built in 1.29s`  
**Status**: Verified & Operational  

---

## 1. Executive Summary

**Stage H — Monitoring + Incidents + Enterprise Governance** delivers a unified operational interface for security administrators, SOC analysts, and auditors. It clearly bifurcates the user experience into:

1. **Normal Workspace**: Simple Home (`/`), Scan Console (`/scans`), Ask SECUROXI (`/ask`), and Candidate Screening (`/screening`).
2. **Security Operations & Governance**:
   * **Security Monitoring** (`/monitoring`): Real-time subsystem health, telemetry throughput, and activity stream.
   * **Incident Center** (`/incidents`): Authoritative 6-stage lifecycle board (`DETECTED` $\to$ `TRIAGED` $\to$ `INVESTIGATING` $\to$ `RESPONDED` $\to$ `RESOLVED` $\to$ `CLOSED`).
   * **Policy Center** (`/policies`): Declarative rule governance labeled `POLICY AUTHORITY`.
   * **Audit Trail** (`/audit`): Searchable, tenant-scoped compliance log with zero secret leakage.
   * **Administration & Settings** (`/settings`): RBAC roles, safe one-time API key reveals, and data retention policies.

---

## 2. Information Architecture & Navigation

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ NORMAL WORKSPACE (Recruiters, Document Reviewers, General Users)                                │
│                                                                                                 │
│  [ Home ]  •  [ Scan Files ]  •  [ Scan Folder ]  •  [ Ask SECUROXI ]  •  [ Screening ]         │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ SECURITY OPERATIONS & GOVERNANCE (Security Admins, SOC Analysts, Compliance Officers)            │
│                                                                                                 │
│  • Security Operations (/overview)            • Security Brain (/security-brain)                │
│  • Security Monitoring (/monitoring)          • Incident Response (/incidents)                  │
│  • Policy Engine (/policies)                  • Audit Trail (/audit)                            │
│  • ATS Integrations (/ats)                    • Admin & Settings (/settings)                    │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Subsystem Health & Degraded State Experience

| Subsystem | Health Status | Degraded Behavior |
| :--- | :---: | :--- |
| **Security Engine** | `HEALTHY` | Fails closed; uninspected payloads quarantined |
| **Document Processing** | `HEALTHY` | Ingests queued files asynchronously with backpressure |
| **Database & Vector Store** | `HEALTHY` | In-memory sqlite fallback in standalone environments |
| **Event Bus & SIEM Stream**| `HEALTHY` | Local ring-buffer spooling until reconnection |
| **ATS Webhook Connectors** | `HEALTHY` | Retries webhook receipt with HMAC signature check |

> **Degraded-State UX Invariant**: If the LLM/reasoning layer is offline, the interface displays: *"AI advisory unavailable. Deterministic security scanning and policy rules remain operational."*

---

## 4. Incident Response Lifecycle Board

```text
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  1. DETECTED │──►│  2. TRIAGED  │──►│ 3. INVESTIG. │──►│ 4. RESPONDED │──►│ 5. RESOLVED  │──►│  6. CLOSED   │
│              │   │              │   │              │   │              │   │              │   │              │
│ Auto-flagged │   │ Severity &   │   │ Forensic &   │   │ Playbook &   │   │ Root cause   │   │ Post-mortem  │
│ by Security  │   │ risk scored  │   │ Brain graph  │   │ quarantine   │   │ mitigated    │   │ archived     │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
```

---

## 5. Security & Privacy Invariants

1. **Policy Authority**: Clearly marked `POLICY AUTHORITY` to reinforce that policies—not language models—authorize high-impact security actions.
2. **Safe API Key Ingress**: When an API key is generated in `/settings`, the raw secret is presented once in a modal with explicit instructions: *"Store this key securely. It will not be shown again."*
3. **Tenant Isolation**: Audit logs, scan metrics, and incident boards enforce `tenant_id` boundaries on all queries.
4. **Data Retention**: Configurable document, scan, and audit log retention with automated database purge execution.

---

## 6. Verification & Test Suite

* **Integration Suite**: [`tests/test_monitoring_incidents_governance.py`](file:///Users/jashanpreetsingh/Downloads/SECUROXI/tests/test_monitoring_incidents_governance.py) validates health probes, incident lifecycle storage, audit trail logging, and retention purge (`253 / 253 passed`).
* **Frontend Production Build**: `tsc && vite build` bundled cleanly in `1.29s`.
