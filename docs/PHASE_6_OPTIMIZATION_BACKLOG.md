# SECUROXI AI — Phase 6 Prioritized Optimization Backlog (Stage 28)

**Version**: v2.0.0-phase6-backlog  
**Scope**: Targeted, Data-Driven Performance & Cost Optimizations for Stages 29+  

---

## 1. Prioritized Optimization Items

| Backlog ID | Priority | Target Subsystem | Confirmed Root Cause | Proposed Change | Expected Benefit | Target Stage |
| :--- | :---: | :--- | :--- | :--- | :--- | :---: |
| **OPT-01** | **HIGH** | Hybrid Reranker | Full cross-encoder pass over unpruned candidate sets | Vector distance pre-filtering & top-k pruning before cross-encoder | ~40% reduction in reranking latency | **Stage 29** |
| **OPT-02** | **HIGH** | Retrieval Planner | Fixed multi-hop execution on simple direct questions | Dynamic early-stop condition on sufficient Hop 1 evidence | ~30% reduction in query latency & token cost | **Stage 29** |
| **OPT-03** | **MEDIUM**| Groundedness Verifier | Redundant verification passes for identical claims | Claim hash de-duplication and batched verification | ~25% reduction in verification cost | **Stage 29** |
| **OPT-04** | **MEDIUM**| Hiring Screener | Reasoning evaluated on unquarantined malicious candidates | Strict pre-screening security gate execution | Saves LLM calls on high-risk files | **Stage 29** |

---

## 2. Invariants & Guardrails

- **Zero Security Degradation**: No optimization may bypass the SecuroxiScanner, Security Brain, or enterprise policy checks.
- **Citation Integrity**: All verified claims must retain valid source citation links (`[CIT-1]`).
- **Tenant Isolation**: Optimization caching or indexing must remain strictly isolated per tenant.
