# SECUROXI AI Phase 5 Stage 2 — Enterprise Application Shell & Navigation Specification

**Engine Version**: `0.5.0-application-shell`  
**Classification**: **`ENTERPRISE FRONTEND SHELL & NAVIGATION SPECIFICATION`**  
**Stage 2 Status**: **`PASS`**  
**Date**: `2026-08-14`

---

## 1. Application Shell & Navigation Architecture

The **SECUROXI Enterprise Shell** provides a high-density, dark-first navigation layout with grouped navigation items, tenant context switching, global search entry points, and responsive layout drawer behavior:

```
[Header: Breadcrumb / Global Search / Tenant Selector / Notifications / Profile]
───────────────────────────────────────────────────────────────────────────────
[Sidebar Navigation: Grouped Items]   │ [Main Page Container]
- SECURITY & DEFENSE                   │
  * Overview (/overview)              │ - Header Bar
  * Security Brain (/security-brain)  │ - Active Route Component Render Area
  * Incidents (/incidents)            │ - Loading / Error / Empty States
  * Scan Console (/scans)             │
- INTELLIGENCE & SCREENING             │
  * Candidate Screening (/screening)  │
  * Documents (/documents)            │
  * ATS Connectors (/ats)             │
  * Continuous Monitoring (/monitoring)│
- GOVERNANCE & CONTROL                 │
  * Policy Engine (/policies)         │
  * Audit Trail (/audit)              │
  * Settings (/settings)              │
  * Design System (/design-system)    │
```

---

## 2. Primary Navigation Groups

1. **SECURITY & DEFENSE** (Priority High-Visibility Group):
   - **Overview** (`/overview`): System risk summary and threat telemetry.
   - **Security Brain** (`/security-brain`): AI reasoning layer and attack graph visualization.
   - **Incidents** (`/incidents`): Real-time triaged security events and automated responses.
   - **Scan Console** (`/scans`): On-demand layout-aware PDF and document threat scanner.
2. **INTELLIGENCE & SCREENING**:
   - **Candidate Screening** (`/screening`): Security-aware resume-to-JD semantic fit scoring.
   - **Documents** (`/documents`): Repository of ingested candidate resumes and job specs.
   - **ATS Connectors** (`/ats`): Integrations for Greenhouse, Lever, and enterprise storage.
   - **Continuous Monitoring** (`/monitoring`): Real-time event ingestion pipeline telemetry.
3. **GOVERNANCE & CONTROL**:
   - **Policy Engine** (`/policies`): Deterministic security policy rules and RBAC controls.
   - **Audit Trail** (`/audit`): Multi-tenant audit logs with tenant isolation filters.
   - **Settings & Control** (`/settings`): Organization settings, API keys, and retention rules.
   - **Design System** (`/design-system`): Live UI primitive component showcase.

---

## 3. Responsive Breakpoints

| Viewport Width | Sidebar State | Header Search Bar | Mobile Drawer |
| :--- | :--- | :--- | :--- |
| **Desktop (> 1024px)** | Expanded (260px) | Visible (320px) | Disabled |
| **Tablet (768px - 1024px)**| Collapsible (64px) | Visible | Disabled |
| **Mobile (< 768px)** | Collapsed / Hidden | Hidden | Slide-Out Overlay |

---

## 4. Empirical Test Results (171 Tests)

```text
======================= 171 passed in 2.09s ========================
```
* **Grouped Navigation Routes**: `11 Routes Defined & Accessible` 🟢
* **Tenant Context Switching**: `Stateful Tenant Selector Mounted` 🟢
* **Responsive Layout Rules**: `Desktop, Tablet & Mobile Breakpoints Implemented` 🟢
* **Backend API Compatibility**: `171 / 171 Backend Security Tests Passed (100%)` 🟢

---

## 5. Stage 2 Status

# **`PASS`**
