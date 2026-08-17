# SECUROXI AI — Production Security Incident Response Runbook

**Engine Version**: `v1.0.0`  
**Classification**: **`CONFIDENTIAL OPERATIONAL INCIDENT RUNBOOK`**  
**Audience**: **`SOC Security Analysts, Incident Commanders, SysAdmins`**  
**Date**: `2026-08-14`

---

## 1. Incident Severity & Triage Classification

| Severity Level | Response SLA | Triggers | Containment Protocol |
| :--- | :--- | :--- | :--- |
| **P1 - CRITICAL** | `< 15 Mins` | Indirect Prompt Injection attempting tool hijacking / data exfiltration | Auto-enforce `BLOCK` or `QUARANTINE_DOCUMENT`, isolate tenant ID, preserve audit trace |
| **P2 - HIGH** | `< 30 Mins` | Visual Deception / Micro-text attack or repeated attack pattern correlated ($\ge 3$ occurrences) | Quarantine document, create incident ticket in SOC dashboard |
| **P3 - MEDIUM** | `< 2 Hours` | Webhook signature failure or rate-limit trigger spike | Temporarily block source IP, inspect ATS adapter logs |
| **P4 - LOW** | `< 24 Hours` | Minor format anomaly or clean candidate screening review | Log audit event, standard analyst review |

---

## 2. Emergency Incident Response Workflows

### Scenario A: Indirect Prompt Injection / Instruction Hijacking Detected
1. **Detection**: Security Brain generates signal `INSTRUCTION_OVERRIDE` or `SYSTEM_PROMPT_MANIPULATION` with Risk Score 85+.
2. **Automated Enforcement**: Deterministic Policy Engine automatically overrides LLM recommendations and enforces `BLOCK` or `QUARANTINE_DOCUMENT`.
3. **Analyst Inspection**: Navigate to SOC Threat Workspace (`/incidents`), select Incident ID, inspect exact monospaced evidence snippets and PyMuPDF bounding box spans.
4. **Tenant Containment**: Verify multi-tenant isolation prevents cross-tenant payload propagation.

### Scenario B: Database or Redis Broker Network Interruption
1. **Detection**: Health probe `/api/v1/health/readiness` returns status `degraded`.
2. **System Fail-Safe**: `ContinuousEventBus` gracefully buffers events in fallback memory queue.
3. **Restoration**: Restart database or broker containers:
   ```bash
   docker-compose restart securoxi-postgres securoxi-redis
   ```

---

## 3. Contact & Escalation Protocol

* **Security Operations Center (SOC)**: `soc@securoxi.com`
* **Incident Commander**: `incident-commander@securoxi.com`
