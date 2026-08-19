# SECUROXI AI — Production Operations Runbook (Stage 25)

**Version**: v2.0.0-runbook  
**Audience**: Site Reliability Engineers (SRE), Cloud Operations, Security Administrators  

---

## 1. Routine Operational Procedures

### 1.1 Service Startup
```bash
# 1. Validate environment configuration
python3 -c "from securoxi.environment import validate_environment; print(validate_environment())"

# 2. Launch production stack
docker compose -f docker-compose.prod.yml up -d
```

### 1.2 Health Verification
```bash
# Check container status
docker ps

# Check API readiness probe
curl -f http://localhost:8000/api/v1/health/readiness
```

### 1.3 Graceful Shutdown
```bash
docker compose -f docker-compose.prod.yml stop -t 30
```

---

## 2. Incident Response & Troubleshooting

### 2.1 Degraded Database Connection
- **Symptom**: `/api/v1/health/readiness` returns status `"degraded"`.
- **Mitigation**:
  1. Inspect PostgreSQL logs: `docker logs securoxi-postgres`
  2. Verify database connection string in `DATABASE_URL`.
  3. Ensure persistent volume `/app/data` has available disk space (`df -h`).

### 2.2 AI Provider Outage / Degraded Inference
- **Symptom**: Background research tasks fail with timeout or provider rate limits.
- **Mitigation**:
  1. Switch `AI_PROVIDER` to `mock` or fallback provider.
  2. Restart SECUROXI API container to reload configuration without state loss.

### 2.3 Failed or Stale Task Recovery
- **Symptom**: Tasks remain in `WAITING_FOR_APPROVAL` past expiration.
- **Action**: The Governance Workspace automatically transitions expired proposals to `EXPIRED`. Re-trigger or re-submit the task from Command Workspace.

---

## 3. Phase 8 Autonomy Emergency Procedures & Kill Switches

### 3.1 Global Autonomy Safe Mode Activation (Kill Switch)
- **Objective**: Instantly halt all autonomous actions across the entire enterprise, reverting all operations to recommendation-only without degrading underlying security detection or event collection.
- **Procedure**:
  ```python
  from securoxi.enterprise.autonomy import ControlledAutonomyEngine
  autonomy_engine = ControlledAutonomyEngine()
  autonomy_engine.set_safe_mode(True)
  ```

### 3.2 Provider-Specific Write Lock & Reconciliation
- **Objective**: Freeze external mutations to a misbehaving external ATS or service while continuing read-only ingestion.
- **Procedure**:
  1. Set provider state to `READ_ONLY` in Customer Configuration Workspace.
  2. Initiate state reconciliation to compare internal expected states with external provider states.
  3. Resolve detected `STATE_DRIFT` through governed manual review.

