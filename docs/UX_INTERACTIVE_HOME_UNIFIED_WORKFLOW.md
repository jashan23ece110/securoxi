# SECUROXI AI — Interactive Home & Unified Workflow Architecture

**Document Version**: v1.0.0 Enterprise  
**Repository**: [`https://github.com/jashan23ece110/securoxi.git`](https://github.com/jashan23ece110/securoxi.git)  
**Primary Entrypoint**: `/` (`HomePage`)  

---

## 1. Product UX Vision & Architecture

The SECUROXI Home experience is designed around a single core question:

> **"What do you want to do?"**

Rather than confronting users with dashboard metrics, threat graphs, and SOC panels on initial entry, the home interface serves as a focused task launcher presenting **four primary action cards**:

1. **SCAN FILES**: Single or multi-document ingestion checking for prompt injection, micro-text, and visual deception.
2. **SCAN FOLDER**: Large-scale folder discovery and distributed streaming scan.
3. **ASK SECUROXI**: Grounded, citation-backed document intelligence Q&A.
4. **HIRING / ATS**: Candidate resume security gating and calibrated fit scoring.

---

## 2. Interactive In-Place Workspace Model

When a user selects an action card:
- The selected workflow **expands directly into the primary content area**.
- The remaining three actions collapse into a responsive top navigation selector (`All Tasks`, `Scan Files`, `Scan Folder`, `Ask SECUROXI`, `Hiring / ATS`).
- Users transition smoothly between tasks without losing their current state or context.

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ SECUROXI AI • What do you want to do?                                                           │
│ [ ← All Tasks ]   [ 📁 Scan Files ]   [ 📂 Scan Folder ]   [ 💬 Ask SECUROXI ]   [ 👥 Hiring/ATS ]│
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                 │
│  SELECTED WORKFLOW WORKSPACE                                                                    │
│  - Focused controls & real-time telemetry                                                       │
│  - Upstream Security Gate evaluation                                                            │
│  - Actionable next steps based on verdict                                                       │
│                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Workflow Specifications

### A. Scan Files Workspace
- **Supported Formats**: `PDF`, `DOCX`, `TXT`, `HTML`, `PNG`, `JPG`.
- **Processing Stepper**: `1. VALIDATING` $\to$ `2. PARSING` $\to$ `3. SECURITY ANALYSIS` $\to$ `4. RISK EVALUATION` $\to$ `5. COMPLETE`.
- **Verdict Gate & Next Actions**:
  - **`SAFE`**: Displays green clearance banner. Unlocks downstream trusted actions:
    - `[ Screen Against a Job ]`: Runs instant qualification against target JD (e.g. *Senior Cloud Security Engineer*, Fit: 94.2/100).
    - `[ Send to Hiring / ATS ]`: Hands off to ATS screening pipeline.
    - `[ Ask About This Document ]`: Pre-scopes Ask SECUROXI to the document.
    - `[ View Details ]`: Opens Forensic Document Viewer.
  - **`HIGH_RISK`**: Displays red quarantine banner with exact risk score and extracted malicious evidence. Unlocks:
    - `[ View Document in Forensic Viewer ]` (with spatial bounding boxes).
    - `[ Investigate in Security Brain ]` (with causal attack graph).
    - `[ View Incident ]`.
  - **`UNINSPECTABLE`**: Displays yellow warning banner (*"DOCUMENT NOT FULLY INSPECTABLE"*). Held in review state; **never marked SAFE**.

### B. Scan Folder Workspace
- **Pre-Flight Discovery**: Files found, supported formats, unsupported files, and duplicate hashes skipped.
- **Real-Time Streaming**: Live category counters (`SAFE`, `SUSPICIOUS`, `HIGH_RISK`, `UNINSPECTABLE`, `FAILED`).
- **Completion Actions**: `[ View High Risk ]`, `[ View All Results ]`, `[ Ask About This Folder ]`.

### C. Ask SECUROXI Workspace
- **Scoped Natural Language Retrieval**: Anti-prompt-injection XML-fenced context assembly.
- **Progressive Execution**: `Authorizing Scope` $\to$ `Searching Documents` $\to$ `Verifying Quarantine` $\to$ `Building Grounded Answer`.
- **Grounded Citations**: Source document name, page number, confidence match, and deep-link to `/investigate`.

### D. Hiring / ATS Workspace
- **Strict Separation of Invariants**:
  - `Security Status` (`SAFE`, `HIGH_RISK`, `UNINSPECTABLE`) determines document trust.
  - `Calibrated Fit Score` (`94.2 / 100`) measures Job Description alignment.
  - `HIGH_RISK` candidate is frozen at Rank #0 with Fit Score = 0.0 and quarantined from ATS advance.

---

## 4. Preservation of Advanced Operations

All advanced security, governance, and forensic routes remain fully accessible via the top navigation and deep links:
- `/overview`: Security Operations Console
- `/security-brain`: Threat causality & Attack Graphs
- `/investigate`: Spatial Forensic Viewer
- `/incidents`: 6-stage Incident Lifecycle board
- `/monitoring`: Subsystem health & event stream
- `/policies`: Declarative Policy Authority
- `/audit`: Searchable compliance logs
- `/settings`: RBAC & API key governance
