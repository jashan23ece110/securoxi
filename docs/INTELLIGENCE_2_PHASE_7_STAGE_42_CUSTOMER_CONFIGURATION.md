# SECUROXI AI Intelligence 2.0 — Phase 7 Stage 42: Customer-Level Policies, Configuration & Intelligence Controls

**Version**: v2.0.0-phase7-stage42  
**Test Baseline**: **`537 / 537 PASSED`** (3 new Configuration tests + 534 existing regression tests)  
**Status**: **CUSTOMER CONFIGURATION CONTROLS OPERATIONAL** 🟢  

---

## 1. Executive Summary & Configuration Architecture

Stage 42 establishes a canonical, typed, and hierarchical customer policy & configuration management engine:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   ENTERPRISE CUSTOMER CONFIGURATION PIPELINE           │
│ Platform Baseline → Organization Setting → Workspace Override          │
│ → Safety Boundary Validation (Min / Max / Invariants) → Effective Value│
├────────────────────────────────────────────────────────────────────────┤
│ • Canonical Registry: Bounded settings across 7 categories             │
│ • Immutable Invariants: Foundational security rules strictly protected │
│ • Hierarchical Inheritance: Org defaults with Workspace overrides     │
│ • Dry-Run Simulation: Test changes on workflows without side effects   │
│ • Immutable Audit Logs: Versioned history for rollbacks & compliance   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Setting Registry & Safety Boundaries

| Setting Key | Category | Default | Allowed Range / Choices | Description |
| :--- | :---: | :---: | :---: | :--- |
| `max_retrieval_hops` | `RETRIEVAL` | `3` | `1` to `20` | Max RAG multi-hop retrieval depth |
| `default_task_budget_usd` | `TASKS` | `10.0` | `1.0` to `100.0` | Autonomous task cost ceiling |
| `shortlist_default_size` | `HIRING` | `20` | `1` to `100` | Target candidate shortlist volume |
| `require_ats_write_approval` | `GOVERNANCE` | `True` | `[True, False]` | ATS stage mutation approval requirement |
| `ai_behavior_profile` | `AI_INTELLIGENCE` | `BALANCED` | `FAST`, `BALANCED`, `DEEP` | AI reasoning depth & latency profile |
| `security_review_threshold` | `SECURITY` | `0.75` | `0.50` to `0.95` | Sensitivity threshold (Platform floor: 0.50) |

---

## 3. Implementation Details

1. **`EnterpriseConfigurationManager` (`securoxi/enterprise/config/manager.py`)**:
   - Computes effective hierarchical configurations and validates bounds.
2. **Immutable Security Invariants (`FORBIDDEN_SETTINGS`)**:
   - Strictly rejects attempts to modify foundational security invariants (`security_authority`, `policy_bypass`, `mark_high_risk_as_safe`).
3. **Dry-Run Simulation (`SimulationResult`)**:
   - Enables admins to preview effective values and identify affected workflows prior to persistent activation.
