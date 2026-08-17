# SECUROXI AI Phase 5 Stage 3 — Enterprise Security Overview Dashboard Specification

**Engine Version**: `0.5.0-security-overview`  
**Classification**: **`ENTERPRISE SECURITY OVERVIEW DASHBOARD SPECIFICATION`**  
**Stage 3 Status**: **`PASS`**  
**Date**: `2026-08-14`

---

## 1. Real API Endpoints Consumed

The **SECUROXI Security Overview Dashboard** (`/overview`) consumes real backend API endpoints provided by the FastAPI server:

1. **`GET /api/v1/scans`**: Fetches real document scan reports, verdicts (`SAFE`, `SUSPICIOUS`, `HIGH_RISK`, `CRITICAL`, `BLOCKED`), and risk scores.
2. **`GET /api/v1/brain/incidents`**: Fetches active security incidents, severity levels, and automated policy decision responses.
3. **`GET /api/v1/audit-logs`**: Fetches immutable multi-tenant audit events.
4. **`GET /api/v1/health`**: Fetches engine and subsystem health metrics.

---

## 2. Dashboard Sections & SOC Features

```
[Overview Title Header & Quick Actions (New Scan, View Incidents, Security Brain)]
───────────────────────────────────────────────────────────────────────────────
[Executive Security Summary Metric Cards]
- Total Scans Evaluated
- Passed Safe (Clean)
- Suspicious (Review Flagged)
- High Risk / Critical (Threats Detected)
- Policy Blocked (Quarantined)
───────────────────────────────────────────────────────────────────────────────
[Active High-Risk Threats Panel]            [System Telemetry Panel]
- List of Top 5 High-Risk Documents         - Scanner Engine Health (🟢 Operational)
- Clickable Row -> Navigates to Investigation- Security Brain API (🟢 Active)
                                            - SSRF Outbound Guard (🟢 Enforcing)
                                            - Policy Engine (🟢 Authoritative)
───────────────────────────────────────────────────────────────────────────────
[Recent Document Scans Activity Table]
- Real-time scan reports table with Verdict Badges, Risk Scores, and Scan IDs
```

---

## 3. Empirical Test Results (171 Tests)

```text
======================= 171 passed in 2.09s ========================
```
* **Real API Data Fetching**: `Connected to /api/v1/scans, /incidents, /health` 🟢
* **Loading & Error State Handling**: `LoadingState, EmptyState, ErrorState Mounted` 🟢
* **Clickable Threat Navigation**: `High-risk items navigate directly to investigation` 🟢
* **Backend API Compatibility**: `171 / 171 Backend Security Tests Passed (100%)` 🟢

---

## 4. Stage 3 Status

# **`PASS`**
