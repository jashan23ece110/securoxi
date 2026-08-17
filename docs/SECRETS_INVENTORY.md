# SECUROXI AI — Enterprise Secrets Inventory Specification

**Engine Version**: `0.5.0-secrets-inventory`  
**Classification**: **`SECRETS INVENTORY & RISK AUDIT REPORT`**  
**Audit Date**: `2026-08-14`

---

## 1. Secret Inventory & Audit Classification

*(Note: In accordance with enterprise security controls, zero actual secret key values are printed in this document).*

| Secret Identifier | Category | Primary Location | Exposure Risk | Recommended Storage Provider |
| :--- | :--- | :--- | :--- | :--- |
| **`SECUROXI_API_KEY`** | Client Auth Key | `securoxi/api/app.py` | HIGH | Vault / AWS Secrets Manager |
| **`GEMINI_API_KEY`** | LLM Provider Key | `securoxi/ai_reasoning/provider.py` | CRITICAL | Vault / AWS Secrets Manager |
| **`DATABASE_URL`** | Database Credentials | `securoxi/storage/db.py` | HIGH | Vault / AWS Secrets Manager |
| **`REDIS_URL`** | Event Broker Credentials | `securoxi/brain/continuous_monitoring.py` | HIGH | Vault / AWS Secrets Manager |
| **`GREENHOUSE_WEBHOOK_SECRET`** | Webhook Signing Secret | `securoxi/integrations/ats_adapters.py` | MEDIUM | Vault / AWS Secrets Manager |
| **`LEVER_WEBHOOK_SECRET`** | Webhook Signing Secret | `securoxi/integrations/ats_adapters.py` | MEDIUM | Vault / AWS Secrets Manager |
| **`CLOUD_STORAGE_CREDENTIALS`** | Cloud Connector Auth | `securoxi/integrations/cloud_connectors.py` | HIGH | AWS Secrets Manager / GCP KMS |

---

## 2. Exposure Prevention & Masking Audit

* **Source Code Verification**: Zero plaintext production API keys or passwords are hardcoded in application source.
* **Log Masking Verification**: Secret strings are masked (`secu***`) before logging or audit trail insertion.
* **Docker Image Layers**: Docker images do not bake secret values into container layers; secrets are injected dynamically at runtime via environment variables or secret volumes.

---

## 3. Status Decision Choice

# **`PASS`**
