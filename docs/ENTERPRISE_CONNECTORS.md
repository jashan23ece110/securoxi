# SECUROXI AI Phase 3 — Enterprise Data & Cloud Connectors Architecture Specification

**Engine Version**: `0.3.0-connectors`  
**Classification**: **`ENTERPRISE CONNECTOR ARCHITECTURE SPECIFICATION`**  
**Stage 6 Status**: **`PASS`**  
**Date**: `2026-08-14`

---

## 1. Connector Architecture Overview

The **SECUROXI Enterprise Connector Framework** provides a provider-agnostic abstraction (`BaseConnector`) allowing SECUROXI to ingest documents and events from local filesystems, ZIP archives, cloud object storage, and cloud drives.

```
+-------------------------------------------------------------------+
|               SECUROXI DATA & CLOUD CONNECTORS                    |
|                                                                   |
|  LocalFileConnector    --->  Local Directory & ZIP Archive Scanner|
|  ObjectStorageConnector--->  AWS S3 / Azure Blob Storage Mock     |
|  CloudDriveConnector  --->  Google Drive / OneDrive Mock         |
|  APIUploadConnector    --->  REST API Upload Endpoint Source      |
+-------------------------------------------------------------------+
                                   |
                                   v
+-------------------------------------------------------------------+
|               NORMALIZED STORAGE EVENT STREAM                     |
|  - event_type: FILE_CREATED | FILE_MODIFIED | FILE_DELETED        |
|  - content_hash_sha256: SHA-256 Content Hash                      |
|  - provenance_path: Full File/Object URI Provenance Location      |
+-------------------------------------------------------------------+
                                   |
                                   v
+-------------------------------------------------------------------+
|               SECUROXI SECURITY GATE & PIPELINE                   |
|               (Mandatory Phase 1 Scan Gate)                       |
+-------------------------------------------------------------------+
```

---

## 2. Core Capabilities & Supported Sources

1. **Local Disk & ZIP Archive Source (`LocalFileConnector`)**: Scans directories for `.pdf`, `.txt`, `.docx`, and `.zip` archives.
2. **Object Storage (`ObjectStorageConnector`)**: Connects to AWS S3 or Azure Blob Storage buckets, tracking bucket object metadata and file content hashes.
3. **Cloud Drive (`CloudDriveConnector`)**: Monitors Google Drive / OneDrive change events (`FILE_CREATED`, `FILE_MODIFIED`, `FILE_DELETED`).
4. **SHA-256 Content Deduplication**: `is_duplicate_content(content_hash)` prevents redundant scanning of identical document bytes across multiple connectors.
5. **Connector Health Checks**: `health_check()` reports `HEALTHY`, `DEGRADED`, `EXPIRED_CREDENTIALS`, or `UNREACHABLE`.

---

## 3. Security Controls

* **Credential Isolation**: Credentials (`access_key`, `secret_key`) are isolated in `ConnectorConfig` objects and excluded from default log traces.
* **Expired Credentials Handling**: Expired secrets trigger `ConnectorHealthStatus.EXPIRED_CREDENTIALS` and raise `PermissionError` immediately on fetch attempts.
* **Inaccessible File Failure Isolation**: Missing or deleted storage objects raise `FileNotFoundError` or `KeyError` safely without crashing the pipeline.

---

## 4. Empirical Test Results (119 Tests)

```text
======================= 119 passed in 1.04s ========================
```
* **Phase 1 Security Engine Tests**: `57 / 57 PASSED`
* **Phase 2 Screening Engine Tests**: `35 / 35 PASSED`
* **Phase 3 Stage 1 Brain Core Tests**: `4 / 4 PASSED`
* **Phase 3 Stage 2 Threat Intel Tests**: `3 / 3 PASSED`
* **Phase 3 Stage 3 Runtime Security Tests**: `6 / 6 PASSED`
* **Phase 3 Stage 4 Policy Engine Tests**: `5 / 5 PASSED`
* **Phase 3 Stage 5 ATS Integration Tests**: `5 / 5 PASSED`
* **Phase 3 Stage 6 Connectors Tests**: `4 / 4 PASSED`
* **Total Suite**: **`119 / 119 PASSED (100%)`**

---

## 5. Known Limitations

1. **Mock S3/Drive Storage Default**: Real S3/Drive SDK connections use local mock bucket buffers during test/staging execution to avoid cloud infrastructure dependencies.

---

## 6. Phase 3 Stage 6 Status

# **`PASS`**
