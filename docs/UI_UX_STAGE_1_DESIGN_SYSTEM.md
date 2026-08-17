# SECUROXI AI — UI/UX Stage 1: Visual Research & Design System Specification

**Stage**: UI/UX Stage 1 — Visual Research + SECUROXI Design System  
**Status**: Verified & Operational  
**Test Baseline**: `226 / 226 PASSED`  
**Frontend Compilation**: `tsc && vite build` $\rightarrow$ `built in 780ms`  
**Workspace**: `/Users/jashanpreetsingh/Downloads/SECUROXI`

---

## 1. Visual Direction & Design Philosophy

SECUROXI AI is designed as an **authoritative, data-dense enterprise AI defense and SOC platform**. It avoids frivolous consumer AI patterns (oversized glowing blobs, fake AI typing animations, low-density card grids) in favor of **precision, high-contrast evidence rendering, technical depth, and deterministic clarity**.

---

## 2. Reference Resources & Architectural Adaptation

| Resource | Purpose | Selective Adaptation into SECUROXI |
| :--- | :--- | :--- |
| **`https://uiverse.io/`** | Micro-interactions & Primitives | Adapted high-precision button active states, toggle switch micro-transitions, input focus glows (`0 0 12px rgba(6, 182, 212, 0.2)`), and data table hover rows. |
| **`https://fffuel.co/`** | SVG Backgrounds & Abstract Geometry | Integrated subtle geometric technical dot meshes and grid pattern SVGs (`<BackgroundPattern />`) at low opacity (3–4%) to give depth without visual clutter. |
| **`https://iconbuddy.com/`** | Unified Iconography System | Standardized on **Lucide Icons** across all modules. Enforced strict rules: consistent 1.5–1.75px optical stroke weight, 14–18px standard sizing, zero mixed emoji icons. |
| **`https://webgradients.com/`** | Restrained Accent Gradients | Used subtle linear gradients strictly as functional visual accents (e.g. `--grad-cyan-glow`, `--grad-threat-critical`, `--grad-brain-pulse`), never as distracting full-background fills. |

---

## 3. Standardized Iconography Rules

* **Icon Family**: `lucide-react` (SVG stroke-based vector icons).
* **Rationale**: Lucide provides crisp, mathematically balanced geometric strokes that complement monospace evidence codeblocks and dark technical surfaces.
* **Standard Sizing Matrix**:
  * Micro (inline badges, tooltips): `12px`
  * Small (table headers, inputs, icon buttons): `14px`–`16px`
  * Medium (sidebar links, card headers): `17px`–`18px`
  * Large (empty state anchors, error banners): `24px`–`32px`

---

## 4. Complete Design Token System (`tokens.css`)

### 4.1 Surfaces & Depth Tokens
* Canvas Background: `--bg-app: #070B12`
* Standard Surface: `--bg-surface: #0C121E`
* Elevated Surface: `--bg-surface-elevated: #121A2B`
* Hover Surface: `--bg-surface-hover: #18233A`
* Input Surface: `--bg-input: #090E17`
* Modal/Drawer Overlay: `--bg-overlay: rgba(3, 7, 18, 0.82)`

### 4.2 Borders & Accents
* Subtle Divider: `--border-subtle: #141E32`
* Default Border: `--border-default: #1E2D4A`
* Strong / Active Border: `--border-strong: #2E426B`
* Focus Ring: `--border-focus: #06B6D4`
* Primary Technical Accent: `--accent-cyan: #06B6D4` (Hover: `#0891B2`, Background: `rgba(6, 182, 212, 0.12)`)
* Secondary Intelligence Accent: `--accent-indigo: #6366F1` (Hover: `#4F46E5`)

### 4.3 Security Status & Verdict Taxonomy
| Status Token | Background (`rgba`) | Text Color | Border Color | Operational Meaning |
| :--- | :--- | :--- | :--- | :--- |
| `SAFE` / `ALLOWED` | `rgba(16, 185, 129, 0.12)` | `#10B981` | `rgba(16, 185, 129, 0.35)` | Document clean, zero threats verified. |
| `SUSPICIOUS` | `rgba(245, 158, 11, 0.12)` | `#F59E0B` | `rgba(245, 158, 11, 0.35)` | Formatting anomaly or structural deviation. |
| `HIGH_RISK` | `rgba(239, 68, 68, 0.12)` | `#EF4444` | `rgba(239, 68, 68, 0.35)` | Proven malicious instruction payload. |
| `CRITICAL` | `rgba(220, 38, 38, 0.20)` | `#FCA5A5` | `rgba(220, 38, 38, 0.50)` | Active multi-vector exploit / system override. |
| `BLOCKED` | `rgba(168, 85, 247, 0.14)` | `#A855F7` | `rgba(168, 85, 247, 0.40)` | Enforced quarantine policy execution. |
| `REVIEW` | `rgba(236, 72, 153, 0.14)` | `#EC4899` | `rgba(236, 72, 153, 0.40)` | Flagged for SOC analyst review. |
| `PROCESSING` | `rgba(59, 130, 246, 0.14)` | `#3B82F6` | `rgba(59, 130, 246, 0.40)` | Async bulk processing / OCR in progress. |
| `FAILED` | `rgba(248, 113, 113, 0.14)` | `#F87171` | `rgba(248, 113, 113, 0.40)` | Parse exception or format error. |
| `UNINSPECTABLE` | `rgba(217, 119, 6, 0.16)` | `#D97706` | `rgba(217, 119, 6, 0.45)` | Scanned image / zero text layer quarantine. |

### 4.4 Typography Scale
* Fonts: `Inter` (sans-serif UI), `JetBrains Mono` (code & forensic evidence)
* `--text-xs`: `0.6875rem` (11px) — Micro-copy, line numbers, table tags
* `--text-sm`: `0.75rem` (12px) — Badges, secondary metadata
* `--text-base`: `0.8125rem` (13px) — Body text, table data
* `--text-md`: `0.875rem` (14px) — Primary copy, button labels
* `--text-lg`: `1.000rem` (16px) — Card and panel headers
* `--text-xl`: `1.125rem` (18px) — Section titles
* `--text-2xl`: `1.375rem` (22px) — Metric values
* `--text-3xl`: `1.750rem` (28px) — Page titles

### 4.5 Restrained Radius & Elevation
* Radii: `--radius-xs: 2px`, `--radius-sm: 4px`, `--radius-md: 6px`, `--radius-lg: 8px`, `--radius-xl: 12px`, `--radius-full: 9999px`
* Elevation: High-density dark shadows (`--shadow-sm`, `--shadow-md`, `--shadow-lg`, `--shadow-xl`)

### 4.6 Motion & Accessibility Tokens
* Transitions: `--transition-fast: 120ms`, `--transition-normal: 180ms`, `--transition-slow: 280ms`
* Reduced Motion: Global media query `@media (prefers-reduced-motion: reduce)` disables non-essential animations.

---

## 5. Reusable Component Rules & Inventory

```
frontend/src/components/ui/
├── Alert.tsx               # Dismissible alerts (info, success, warning, danger, critical)
├── BackgroundPattern.tsx   # Subtle SVG geometric dot/grid patterns
├── Badge.tsx               # StatusBadge, SeverityBadge, VerdictBadge across all 10 states
├── Button.tsx              # Primary, secondary, danger, ghost, outline buttons
├── Card.tsx                # Card, StatCard with deltas and trend badges
├── CommandPalette.tsx      # Global Cmd+K searchable command palette
├── DataTable.tsx           # Sortable, paginated high-density forensic table
├── Drawer.tsx              # Slide-over panel for deep forensic span inspection
├── EvidenceBlock.tsx       # Exact evidence codeblock, coordinates, detector, copy button
├── IconButton.tsx          # Accessible icon buttons with tooltips
├── Input.tsx               # Input with icon slots, error states, and clear action
├── Metric.tsx              # Large metric numbers with trend up/down pills
├── Modal.tsx               # Accessible dialog with ESC listener and backdrop blur
├── Panel.tsx               # Collapsible multi-section inspection container
├── RiskIndicator.tsx       # Numerical 0–100 risk score gauge with color mapping
├── States.tsx              # LoadingState, EmptyState, ErrorState, Skeleton
├── Tabs.tsx                # Line and pill tab navigation with count badges
├── Timeline.tsx            # Chronological incident & audit trail
├── Toggle.tsx              # Accessible toggle switch with smooth micro-animation
├── Tooltip.tsx             # Hover explanation tooltip with configurable placement
└── index.ts                # Barrel export
```

---

## 6. Design System Showcase Route (`/design-system`)

The private internal showcase route is available at `/design-system` and includes interactive tabs:
1. **Core Primitives & Status Language**: Standardized 10 status badges, severity badges, button variants, icon buttons with tooltips, and stat cards.
2. **Inputs, Toggles & Controls**: Interactive search input with clear button, API key input, email validation state, and animated security policy toggles.
3. **Security Forensics & Metrics**: Authoritative `EvidenceBlock` examples with copy action, `RiskIndicator` gauges, and collapsible `Panel` inspectors.
4. **Data Tables & Overlays**: Sortable `DataTable`, chronological `Timeline`, interactive `Modal`, and `Drawer`.
5. **Alerts & Component States**: Severity alerts, `LoadingState`, `EmptyState`, and `ErrorState` with retry buttons.

---

## 7. Verification & Quality Assurance

* **TypeScript & Vite Build**: `✓ built in 780ms` (zero compiler warnings or type errors).
* **Backend Pytest Suite**: `226 passed, 5 warnings in 2.41s` (100% pass rate).
* **Route Integrity**: All 12 product routes preserved and fully functional.
