# SECUROXI AI Intelligence 2.0 — Phase 7 Stage 37: Advanced RBAC, Enterprise Identity & SSO

**Version**: v2.0.0-phase7-stage37  
**Test Baseline**: **`521 / 521 PASSED`** (4 new RBAC & Identity tests + 517 existing regression tests)  
**Status**: **ENTERPRISE IDENTITY HARDENED** 🟢  

---

## 1. Executive Summary & Identity Architecture

Stage 37 builds advanced, granular enterprise RBAC, bounded agent delegation, and SSO identity provider verification upon Stage 36's organization and workspace hierarchy:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   ENTERPRISE IDENTITY & RBAC PIPELINE                  │
│ Human / IdP Assertion → IdentityContext → Granular Permissions → Guard │
├────────────────────────────────────────────────────────────────────────┤
│ • Canonical Identity: `IdentityContext` (user, org, ws, roles, perms)  │
│ • Dual Verification Invariant: `RBAC ALLOW + Policy ALLOW = ALLOW`     │
│ • Bounded Agent Delegation: Agents cannot exceed delegating user scope │
│ • Enterprise SSO: OIDC/SAML claim verification & domain verification   │
│ • Immediate Session Revocation & Deny-by-Default enforcement           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Granular Permissions & Role Mapping

```text
ORG_ADMIN          → Full Org, Member, Workspace, Audit, & Policy Management
WORKSPACE_ADMIN    → Workspace-level Resource Management & Screening
RECRUITER          → Candidate Screening, Read, & Export; ATS Read
SECURITY_ANALYST   → Investigations, Evidence, Incidents, & Security Actions
AUDITOR            → Read-Only Audit & Evidence Inspection
MEMBER / GUEST     → Scoped Read & Screening
```

---

## 3. Implementation Details

1. **`EnterpriseRBACManager` (`securoxi/enterprise/identity/rbac.py`)**:
   - Manages role-to-permission mapping, session revocations, and SSO assertion checks.
2. **Bounded Delegation (`DelegationContext`)**:
   - Tasks receive time-limited, scoped delegation allowing agents to execute tool calls on behalf of users without privilege escalation.
3. **Dual Verification Invariant**:
   - RBAC answers whether the user has authorization for the action; deterministic Security Policy answers whether the action is safe. Both must allow for execution to proceed.
