# SECUROXI AI Phase 5 Stage 1 — Frontend Architecture & Design System Specification

**Engine Version**: `0.5.0-frontend-architecture`  
**Classification**: **`ENTERPRISE FRONTEND ARCHITECTURE & DESIGN SYSTEM SPECIFICATION`**  
**Stage 1 Status**: **`PASS`**  
**Date**: `2026-08-14`

---

## 1. Current Frontend Architecture & Migration Strategy

SECUROXI AI previously served a single embedded HTML dashboard from `securoxi/web/static/index.html`. 

In **Phase 5 Stage 1**, we established a modular production-grade **React 18 + TypeScript + Vite** Single Page Application (SPA) architecture inside `frontend/` that compiles into static distribution assets (`securoxi/web/static/dist`) served seamlessly by FastAPI:

```
[Browser Client]
       │
  (GET /overview, /security-brain, /incidents, /scans, /screening, /ats, /design-system)
       │
       ▼
[FastAPI Static SPA Ingress (app.py)] ──▶ Serves securoxi/web/static/dist/index.html
       │
       ▼
[Typed REST API Layer (frontend/src/api/client.ts)]
       │
  (X-API-Key Header + Tenant Isolation)
       │
       ▼
[FastAPI REST API Endpoints (/api/v1/...)]
```

---

## 2. Technology Choices

| Layer | Chosen Technology | Rationale |
| :--- | :--- | :--- |
| **Framework** | **React 18** | High-performance component-based enterprise UI rendering. |
| **Language** | **TypeScript 5.2** | Full static type safety matching backend schemas (`ScanReport`, `Incident`, `PolicyRule`). |
| **Build System** | **Vite 5.1** | Lightning-fast HMR and optimized production bundle output. |
| **Routing** | **React Router DOM v6** | Client-side SPA routing across all 11 enterprise routes. |
| **Design System** | **Custom CSS Tokens** | Dark-first technical security aesthetics with zero external bloat. |

---

## 3. Directory Structure (`frontend/`)

```text
frontend/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
└── src/
    ├── api/
    │   ├── client.ts              # Typed API client for FastAPI backend endpoints
    │   └── types.ts               # Complete TypeScript interfaces matching backend models
    ├── components/
    │   ├── ui/                    # Reusable Design System UI Components
    │   │   ├── Button.tsx
    │   │   ├── Badge.tsx
    │   │   ├── Card.tsx
    │   │   ├── Alert.tsx
    │   │   ├── States.tsx         # LoadingState, EmptyState, ErrorState
    │   │   └── Badge.tsx          # VerdictBadge
    │   └── layout/
    │       ├── AppShell.tsx       # Enterprise Shell
    │       ├── Sidebar.tsx        # 11 Enterprise Routes + Design System Showcase
    │       └── Header.tsx         # Tenant Selector & Engine Health
    ├── styles/
    │   ├── tokens.css             # Foundational Design System CSS variables
    │   └── index.css              # Layout & component styling rules
    ├── pages/
    │   ├── DesignSystemShowcase.tsx # Live Component Showcase Demo Page
    │   └── Placeholders.tsx       # Route Shell Placeholders for all 11 enterprise routes
    ├── App.tsx
    └── main.tsx
```

---

## 4. Design System Tokens & Status Matrix

### Security Verdict & Status Badges
* **`SAFE`**: Emerald Green (`#10B981`, `bg: rgba(16, 185, 129, 0.12)`)
* **`SUSPICIOUS`**: Amber Yellow (`#F59E0B`, `bg: rgba(245, 158, 11, 0.12)`)
* **`HIGH_RISK`**: Red (`#EF4444`, `bg: rgba(239, 68, 68, 0.12)`)
* **`CRITICAL`**: Dark Red (`#DC2626`, `bg: rgba(220, 38, 38, 0.20)`)
* **`BLOCKED`**: Purple (`#9333EA`, `bg: rgba(147, 51, 234, 0.15)`)

---

## 5. Empirical Verification & Test Results

```text
======================= 171 passed in 2.09s ========================
```
* **Frontend SPA Architecture Shell**: `Initialized & Mounted` 🟢
* **Typed API Client**: `Matched to Backend API Schemas` 🟢
* **Design System Showcase (`/design-system`)**: `Rendered & Accessible` 🟢
* **Backend API Compatibility**: `171 / 171 Backend Tests Passed (100%)` 🟢

---

## 6. Stage 1 Status

# **`PASS`**
