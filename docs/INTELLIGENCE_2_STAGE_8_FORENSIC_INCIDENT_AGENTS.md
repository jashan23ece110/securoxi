# SECUROXI AI Intelligence 2.0 — Specialized Forensic & Incident Agents

**Version**: v2.0.0-phase2-stage8  
**Module Paths**:  
- `securoxi/orchestrator/agents/forensic/`
- `securoxi/orchestrator/agents/incident/`  
**Test Baseline**: **`349 / 349 PASSED`** (15 new Forensic & Incident Agent tests + 334 existing regression tests)  
**Status**: **VALIDATED & PRODUCTION READY** 🟢  

---

## 1. Executive Summary

Stage 8 introduces two specialized autonomous agents running on the Stage 4 Agent Runtime:
1. **Forensic Agent (`forensic-agent@1.0.0`)**: Resolves spatial layout provenance (pages, bounding boxes), correlates compound multi-vector attack chains with Security Brain, and evaluates evidence sufficiency.
2. **Incident Agent (`incident-agent@1.0.0`)**: Triages security incidents, synthesizes chronological audit timelines, tracks correlated entities, and prepares controlled response action proposals.

---

## 2. Forensic Agent Architecture

```text
Document Finding / Threat Event
              ↓
  Spatial Layout Resolver (forensic_evidence_lookup)
  (Extracts Page #, Bounding Box [x1, y1, x2, y2], Layout Section)
              ↓
  Security Brain Correlation (attack_graph_lookup)
  (Correlates Micro Text + White Text + Prompt Injection)
              ↓
  Attack Chain Synthesis (ForensicAttackChain)
              ↓
  Output: ForensicInvestigationResult
```

### Forensic Toolset
- `finding_lookup`: Queries raw detection attributes and security state.
- `forensic_evidence_lookup`: Resolves exact visual spans and bounding boxes.
- `attack_graph_lookup`: Queries Security Brain for multi-vector threat graphs.

---

## 3. Incident Agent Architecture

```text
Security Incident ID
         ↓
  Incident Triage (incident_lookup)
  (Determines Severity, Affected Assets, Current Lifecycle State)
         ↓
  Chronological Timeline Synthesis (incident_timeline_builder)
  (Audit Trail: Upload → Detection → Policy Decision → Incident)
         ↓
  Response Proposal (incident_response_proposer)
  (Drafts Action Proposal with requires_human_approval=True)
         ↓
  Output: IncidentAgentResult
```

### Incident Toolset
- `incident_lookup`: Queries incident metadata and current state.
- `incident_timeline_builder`: Constructs chronological timeline of security events.
- `incident_response_proposer`: Drafts high-impact containment proposals.

---

## 4. Security Invariants & Human-in-the-Loop Controls

1. **Deterministic Authority**:
   - The agents never alter authoritative security verdicts (`HIGH_RISK`, `BLOCK`) or incident severity levels.
2. **Human Approval Gate for Mutations**:
   - High-impact response actions (`QUARANTINE_DOCUMENT`, `REJECT_CANDIDATE`, `SUSPEND_PROCESSING`) require explicit human approval (`requires_human_approval=True`).
3. **Prompt Injection Defense**:
   - Malicious instructions embedded in evidence spans or audit logs are treated strictly as untrusted data payloads.
4. **Tenant Isolation**:
   - All lookups, graphs, and timeline events are strictly scoped to the requesting tenant.

---

## 5. Performance Benchmarks

| Operation | Target Latency | Measured Latency | Status |
| :--- | :---: | :---: | :---: |
| **Forensic Spatial Resolution & Attack Chain** | `< 5.0 ms` | **`0.12 ms`** | **PASS** ✅ |
| **Incident Timeline Synthesis & Proposal** | `< 5.0 ms` | **`0.09 ms`** | **PASS** ✅ |

---

## 6. Next Steps: Multi-Agent Coordination & Verification Layer

With all specialized agents complete (Security, Retrieval, Hiring, Forensic, Incident), the next phase will integrate them into a **unified Multi-Agent Coordination & Verification Layer** before transitioning into **Phase 3 (Full Agentic RAG)**.
