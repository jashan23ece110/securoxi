# SECUROXI AI Phase 5 Stage 5 — Threat Investigation & Incident Response Workspace Specification

**Engine Version**: `0.5.0-threat-investigation`  
**Classification**: **`THREAT INVESTIGATION WORKSPACE SPECIFICATION`**  
**Stage 5 Status**: **`PASS`**  
**Date**: `2026-08-14`

---

## 1. Investigation Workflow Architecture

The **SECUROXI Threat Investigation Workspace** (`/incidents`) guides SOC analysts through a complete forensic investigation lifecycle:

```
Threat Listing ──▶ Incident Triaging ──▶ Evidence Inspector ──▶ Attack Graph Nodes ──▶ Policy Decision ──▶ Response Execution
```

---

## 2. Interactive SOC Features

1. **Multi-Criterion Filters**: Filters incident queues by **Severity** (`ALL`, `CRITICAL`, `HIGH`, `MEDIUM`) and **Lifecycle Status** (`DETECTED`, `INVESTIGATING`, `RESPONDED`, `RESOLVED`).
2. **Interactive Node-Selection**: Clicking nodes (Actor, Payload Artifact, Technique, Impact) dynamically reveals node-specific relationship metadata.
3. **Forensic Evidence Inspector**: Displays exact matched pattern strings, detector rule names, risk score evaluations, and enforced policy actions.
4. **Lifecycle Timeline**: Tracks incident timestamps from initial signal detection to automated policy response.

---

## 3. Empirical Test Results (171 Tests)

```text
======================= 171 passed in 2.11s ========================
```
* **Real API Telemetry**: `Connected to /api/v1/brain/incidents & /scans` 🟢
* **Severity & Status Filters**: `Multi-criterion filtering active` 🟢
* **Interactive Node Selection**: `Actor / Artifact / Technique metadata active` 🟢
* **Backend API Compatibility**: `171 / 171 Backend Security Tests Passed (100%)` 🟢

---

## 4. Stage 5 Status

# **`PASS`**
