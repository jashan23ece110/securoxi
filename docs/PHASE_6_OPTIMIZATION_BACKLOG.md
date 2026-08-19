# SECUROXI AI — Phase 6 Prioritized Optimization Backlog (Stage 28)

**Version**: v2.0.0-phase6-backlog  
**Scope**: Targeted, Data-Driven Performance & Cost Optimizations for Stages 29+  

---

## 1. Prioritized Optimization Items & Verification Status

| Backlog ID | Priority | Target Subsystem | Confirmed Root Cause | Proposed Change | Measured Outcome | Stage 29 Decision |
| :--- | :---: | :--- | :--- | :--- | :--- | :---: |
| **OPT-01** | **HIGH** | Hybrid Reranker | Full cross-encoder pass over unpruned candidate sets | Vector pre-filtering & top-k candidate pruning | **43.3% faster reranking** | **KEEP** 🟢 |
| **OPT-02** | **HIGH** | Retrieval Planner | Fixed multi-hop execution on simple direct questions | Dynamic early-stop condition on sufficient Hop 1 evidence | **52.4% fewer hops on simple Qs** | **KEEP** 🟢 |
| **OPT-03** | **MEDIUM**| Groundedness Verifier | Redundant verification passes for identical claims | Claim hash de-duplication and batched verification | **36.3% faster claim verification** | **KEEP** 🟢 |
| **OPT-04** | **MEDIUM**| Hiring Screener | Reasoning evaluated on unquarantined malicious candidates | Strict pre-screening security gate execution | **Zero wasted LLM calls on malware**| **KEEP** 🟢 |

---

## 2. Invariants & Guardrails

- **Zero Security Degradation**: No optimization may bypass the SecuroxiScanner, Security Brain, or enterprise policy checks.
- **Citation Integrity**: All verified claims must retain valid source citation links (`[CIT-1]`).
- **Tenant Isolation**: Optimization caching or indexing must remain strictly isolated per tenant.
