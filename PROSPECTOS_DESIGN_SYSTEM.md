# ProspectOS Design System Specification
**Version:** 2.0.0  
**Status:** Production Standard  
**Design Reference:** Linear, Attio, Stripe Dashboard, Vercel, Notion  

---

## 1. Design Philosophy & Architectural Principles

ProspectOS is an enterprise-grade AI Web Scraping and Lead Intelligence Platform. The user experience is engineered around clarity, precision, restrained elegance, and high-density productivity.

### Core Principles
1. **Light-First Sophistication:** The primary working canvas uses a soft off-white (`#f8fafc`), resting on pure white card surfaces (`#ffffff`) bounded by whisper-thin neutral slate borders (`#e2e8f0`). Heavy black backgrounds, decorative glassmorphism, and neon gradients are strictly banished.
2. **Typography-Driven Hierarchy:** Information hierarchy is established through meticulous font weights and sizing rather than loud colors. Geist Sans provides unmatched readability for operational SaaS interfaces, while Geist Mono anchors technical identifiers, canonical domains, JSON payloads, and timestamps.
3. **Purposeful Semantics:** Colors are strictly functional:
   - **Primary Action:** Professional Blue (`#2563eb`)
   - **AI & Automation:** Restrained Violet/Indigo (`#6366f1` / `#7c3aed`)
   - **Success & Verified:** Emerald (`#059669`)
   - **Warning & Attention:** Amber (`#d97706`)
   - **Destructive & Error:** Crimson (`#dc2626`)
4. **Information Density with Breathing Room:** High data density without visual clutter. Tables, metrics cards, and forms use precise 8px/12px/16px padding grids with rounded corners (`rounded-lg` / `rounded-xl`).
5. **Fluid Motion & Restraint:** Animations are subtle (150ms–200ms ease-out transitions), enhancing state changes without distracting from deep work.

---

## 2. Color Palette & Token System

```css
:root {
  /* Canvas & Surfaces */
  --bg-canvas: #f8fafc;        /* slate-50 */
  --bg-surface: #ffffff;       /* white */
  --bg-subtle: #f1f5f9;        /* slate-100 */
  --bg-elevated: #ffffff;

  /* Borders & Dividers */
  --border-subtle: #f1f5f9;    /* slate-100 */
  --border-default: #e2e8f0;   /* slate-200 */
  --border-strong: #cbd5e1;    /* slate-300 */

  /* Text & Foreground */
  --fg-primary: #0f172a;       /* slate-900 (Deep Navy Charcoal) */
  --fg-secondary: #334155;     /* slate-700 */
  --fg-muted: #64748b;         /* slate-500 */
  --fg-subtle: #94a3b8;        /* slate-400 */

  /* Semantic Interaction */
  --primary-50: #eff6ff;
  --primary-100: #dbeafe;
  --primary-500: #3b82f6;
  --primary-600: #2563eb;      /* Brand Accent */
  --primary-700: #1d4ed8;

  /* AI Intelligence */
  --ai-50: #f5f3ff;
  --ai-100: #ede9fe;
  --ai-600: #7c3aed;
  --ai-700: #6d28d9;

  /* Status Colors */
  --success-bg: #ecfdf5;       /* emerald-50 */
  --success-border: #a7f3d0;   /* emerald-200 */
  --success-text: #047857;     /* emerald-700 */
  --success-dot: #10b981;      /* emerald-500 */

  --warning-bg: #fffbeb;       /* amber-50 */
  --warning-border: #fde68a;   /* amber-200 */
  --warning-text: #b45309;     /* amber-700 */

  --destructive-bg: #fef2f2;   /* red-50 */
  --destructive-border: #fecaca;/* red-200 */
  --destructive-text: #b91c1c;  /* red-700 */
}
```

---

## 3. Typography Hierarchy

### Font Families
- **Primary Body & Display:** `Geist Sans`, `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- **Code, Data & Identifiers:** `Geist Mono`, `ui-monospace, SFMono-Regular, Menlo, monospace`

### Scale & Sizing
| Level | Font Size | Line Height | Weight | Letter Spacing | Use Case |
|---|---|---|---|---|---|
| Display | 28px (1.75rem) | 36px | 700 (Bold) | -0.025em | Major Dashboard Headings |
| Title | 20px (1.25rem) | 28px | 600 (Semibold) | -0.015em | Module Section Titles |
| Subhead | 16px (1.00rem) | 24px | 600 (Semibold) | -0.01em | Card & Modal Titles |
| Body | 14px (0.875rem)| 20px | 400 (Regular) | normal | Standard paragraphs, table cells |
| Small | 12px (0.75rem) | 16px | 500 (Medium) | normal | Metadata, captions, badge text |
| Micro | 11px (0.6875rem)| 14px | 500 / 600 | +0.02em | Badges, timestamps, status labels |

---

## 4. UI Components

### 4.1. Badge Component (`components/ui/badge.tsx`)
Semantic micro-indicators supporting 8 variants, 2 sizes, and optional pulsing status dots.
- `default`: Professional blue tone (`bg-blue-50 text-blue-700 border-blue-200/60`)
- `success`: Emerald tone (`bg-emerald-50 text-emerald-700 border-emerald-200/60`)
- `warning`: Amber tone (`bg-amber-50 text-amber-700 border-amber-200/60`)
- `destructive`: Red tone (`bg-red-50 text-red-700 border-red-200/60`)
- `ai`: Purple tone (`bg-purple-50 text-purple-700 border-purple-200/60`)
- `neutral`: Slate tone (`bg-slate-50 text-slate-700 border-slate-200/60`)
- `secondary`: Subtle slate background
- `outline`: Clean transparent border variant

### 4.2. Card Surface Component (`components/ui/card.tsx`)
Uniform surface abstraction maintaining consistent borders and elevations across the entire application:
- `Card`: Crisp white background (`bg-white`), thin border (`border-slate-200/80`), subtle shadow (`shadow-2xs`), rounded corners (`rounded-xl`).
- `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`.

### 4.3. Navigation Shell (`components/layout/app-shell.tsx`)
- **Collapsible Sidebar:** 256px expanded, 64px collapsed icon-rail mode. Features organized groups:
  - *Workspace:* Overview, Lead Discovery, Templates, Custom Scraper, My Tasks
  - *Lead Intelligence & CRM:* All Leads, Pipeline Board, Lists & Segments, ProspectOS AI Assistant, CRM Analytics, Import / Export
  - *Data Management:* Data Center, Data Cleaning, Export Center
  - *Platform:* Cloud Extraction, Task Scheduler, API & Docs
  - *Administration:* Super Admin Executive Dashboard, Users & Access, Roles & RBAC, Scraper Infrastructure, AI Control Center, SEO Control Center, Platform Settings
- **Sticky Header:** Breadcrumbs route tracking, Global `Cmd+K` command search launcher, System health status pulse ("Services Online"), Notification alerts bell, User profile menu with Role tag.
- **Enterprise Footer:** Status dot, real-time platform latency indicator, documentation links, copyright and system build identifier.
- **Command Palette (`Cmd+K`):** Global modal keyboard-navigable launcher for jumping to any route or executing quick actions.

---

## 5. Responsive Design Standards
- **Desktop (>= 1280px):** Full expanded sidebar, multi-column dashboard grids, side-by-side analytics.
- **Laptop / Tablet (768px – 1279px):** Auto-collapsing sidebar to 64px icon-rail, 2-column KPI cards.
- **Mobile (< 768px):** Slide-over off-canvas mobile drawer, full-width single-column responsive stacking, touch-optimized button targets (minimum 40px height).

