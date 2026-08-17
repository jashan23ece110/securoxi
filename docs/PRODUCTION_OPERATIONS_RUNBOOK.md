# SECUROXI AI — Production Operations & Maintenance Runbook

**Engine Version**: `v1.0.0`  
**Classification**: **`CONFIDENTIAL PRODUCTION OPERATIONS RUNBOOK`**  
**Audience**: **`DevOps Engineers, Systems Administrators, SREs`**  
**Date**: `2026-08-14`

---

## 1. Production Startup, Shutdown & Health Checks

### Startup Command
```bash
docker-compose up -d --build
```

### Shutdown & Service Graceful Restart
```bash
docker-compose down
```

### Health Check Commands
```bash
# Process Liveness Probe
curl -f http://localhost:8000/api/v1/health/liveness

# Dependency Readiness Probe (PostgreSQL & Redis Status)
curl -f http://localhost:8000/api/v1/health/readiness
```

---

## 2. PostgreSQL Backup & Restore Procedures

### Automated Database Backup
```bash
docker exec securoxi-postgres-db pg_dump -U securoxi_user securoxi > securoxi_backup_$(date +%Y%m%d_%H%M%S).sql
```

### Database Restore Procedure
```bash
cat securoxi_backup_20260814_230000.sql | docker exec -i securoxi-postgres-db psql -U securoxi_user -d securoxi
```

---

## 3. Data Retention Purge Execution

Manual execution of data retention purging (cleaning scan reports and audit logs older than retention cutoff):
```bash
python3 -c "from securoxi.storage.db import SecuroxiDatabase; db = SecuroxiDatabase(); print(db.purge_expired_data(retention_days=90))"
```

---

## 4. API Key & Secret Rotation Protocol

1. Update raw secret values in enterprise Secrets Manager (Vault / AWS Secrets Manager).
2. Reload secrets provider configuration via `SecuroxiSecretsManager`.
3. Restart application containers with zero downtime:
   ```bash
   docker-compose restart securoxi-api
   ```
