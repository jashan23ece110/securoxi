# SECUROXI AI Intelligence 2.0 — Phase 7 Stage 38: Enterprise Integrations & ATS Expansion

**Version**: v2.0.0-phase7-stage38  
**Test Baseline**: **`524 / 524 PASSED`** (3 new Enterprise Integration tests + 521 existing regression tests)  
**Status**: **ENTERPRISE INTEGRATIONS READY** 🟢  

---

## 1. Executive Summary & Integration Architecture

Stage 38 standardizes multi-tenant enterprise ATS provider adapters (Greenhouse, Lever, Workday) and governed mutation workflows:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   ENTERPRISE ATS INTEGRATIONS PIPELINE                 │
│ ATS Connection → Automated Capability Discovery → Normalized Entities  │
│ → Scoped Organization Read → Governed Write Proposals (RBAC + Approval) │
├────────────────────────────────────────────────────────────────────────┤
│ • Canonical Adapters: Greenhouse (Full Read/Write), Lever, Workday     │
│ • Normalized Schema: `ExternalJob`, `ExternalCandidate`                │
│ • Multi-Tenant Scoping: Integrations belong strictly to Organization  │
│ • Governed Writes: Natural language / UI actions require proposal,     │
│   RBAC authorization, policy clearance, and human sign-off            │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Provider Capability Matrix

| Provider | Read Jobs | Read Candidates | Read Resumes | Write Stage | Write Notes |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Greenhouse** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Lever** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Workday** | ✅ | ✅ | ✅ | ❌ (Read-only) | ❌ |

---

## 3. Implementation Details

1. **`EnterpriseIntegrationManager` (`securoxi/enterprise/integrations/manager.py`)**:
   - Manages connection lifecycle, multi-tenant isolation, capability discovery, and governed write execution.
2. **Provider Adapters (`securoxi/enterprise/integrations/adapters.py`)**:
   - Normalized provider interfaces for Greenhouse, Lever, and Workday.
3. **Write Governance Workflow (`ATSWriteProposal`)**:
   - Prevents unverified or direct LLM-to-ATS mutations. Actions generate immutable proposals requiring `ATS_WRITE` permissions and `APPROVAL_APPROVE` human sign-off.
