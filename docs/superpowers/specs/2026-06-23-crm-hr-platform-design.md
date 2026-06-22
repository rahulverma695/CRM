# CRM + HR Platform — Design Specification

**Date:** 2026-06-23
**Status:** Approved design, pending implementation plan
**Reference:** [frappe/crm](https://github.com/frappe/crm) (design inspiration only — not a dependency)

---

## 1. Overview

A multi-tenant SaaS platform combining a **sales CRM** and a **mid-range HR system** as two modules of one application. The CRM centers on a visual, drag-and-drop Kanban pipeline, consolidated lead/deal detail pages, and user-defined custom views & filters. The HR module covers employee directory, org chart, attendance, and leave management.

The product targets small-to-medium businesses. CRM is built first; HR second. Both share authentication, user accounts, and the employee↔user link.

**Explicitly out of scope (deferred):** Twilio (removed entirely — no calls/SMS), WhatsApp (deferred to a later phase), HR payroll/performance/recruitment (mid-range scope only).

---

## 2. Goals & Non-Goals

### Goals
- Visual Kanban pipeline with smooth drag-and-drop stage management.
- All-in-one lead/deal detail page: contact details, notes, activity log, tasks.
- User-defined custom views and saved filters (private and shareable).
- Mid-range HR: employee directory, org chart, attendance tracking, leave management with approvals.
- True multi-tenant isolation (SaaS).
- Email+password **and** Google OAuth login.
- An **exceptional, immersive UI** — a defining product requirement, not polish-at-the-end.
- Deployable entirely on free-tier cloud services.

### Non-Goals
- No telephony (Twilio removed).
- No WhatsApp/messaging in initial phases.
- No payroll, performance reviews, recruitment, or shift scheduling.
- No microservices — a single modular monolith.
- No billing/subscription system in initial scope (architecture should not preclude it later).

---

## 3. Architecture

**Pattern:** Modular monolith (chosen over microservices and feature-flagged variants for speed and simplicity at this stage).

### Deployment Topology (free-tier cloud)
- **Frontend:** Vue 3 SPA → **Vercel** (static build, CDN).
- **Backend:** FastAPI → **Render** (REST API + WebSocket server + background workers).
- **Database:** PostgreSQL → **Neon** (with Row-Level Security).

### Backend Stack
- **FastAPI** (async-first; suits WebSockets and webhooks).
- **SQLAlchemy** ORM + **Alembic** migrations.
- **Pydantic** for request/response schemas and validation.
- **python-jose** / **passlib[bcrypt]** for JWT and password hashing.
- **Authlib** (or equivalent) for Google OAuth.

### Backend Module Structure
```
app/
  core/        — auth, tenants, users, permissions, base models, RLS middleware
  crm/         — leads, deals, contacts, pipeline stages, activities, tasks, custom views
  hr/          — employees, departments, attendance, leave types/requests/balances
  main.py      — FastAPI app factory, router registration
  database.py  — SQLAlchemy engine, session, per-request tenant context
```

### Frontend Stack
- **Vue 3** (Composition API, `<script setup>`) + **TypeScript**.
- **Vite** build tool.
- **Vue Router 4** with module-based routes (`/crm/*`, `/hr/*`).
- **Pinia** for state management.
- **TailwindCSS** + CSS variables (design tokens).
- **Motion for Vue** (Framer Motion) for spring/physics animation.
- **vuedraggable** (SortableJS) for the Kanban board.
- **Phosphor Icons** (not Lucide-only).
- Distinctive Google Fonts: **Space Grotesk** (display) + **Outfit** (body).

### Frontend Module Structure
```
src/
  core/        — auth store, tenant store, router guards, API client, design tokens
  crm/         — Kanban, LeadDetail, views, filters, pipeline
  hr/          — Employees, Attendance, Leave, OrgChart
  components/  — shared UI (Button, Modal, Table, Badge, Avatar, Skeleton…)
  router.ts    — /crm/* and /hr/* module routes
```

### Key Cross-Cutting Flows
- **Auth:** Login issues JWT (access + refresh). Claims include `user_id`, `tenant_id`, `role`. Google OAuth resolves to the same JWT flow.
- **Tenant isolation:** FastAPI middleware reads `tenant_id` from the JWT and sets a per-request PostgreSQL session variable (`app.tenant_id`). RLS policies enforce `tenant_id = current_setting('app.tenant_id')` on every table. No cross-tenant leakage is possible at the DB layer.
- **Real-time:** FastAPI WebSocket endpoint with per-tenant rooms. Kanban card moves and activity-feed updates broadcast live to connected clients of the same tenant.

---

## 4. Data Model

All tables include `tenant_id` (FK → `tenants`) and are governed by RLS. Standard audit columns (`created_at`, `updated_at`) are implied on all tables.

### Core (shared)
- **tenants** — `id`, `name`, `slug` (unique), `plan`, `settings` (jsonb), `created_at`.
- **users** — `id`, `tenant_id`, `email`, `name`, `avatar_url`, `role`, `google_id`, `password_hash`, `is_active`, `created_at`.

### CRM
- **pipeline_stages** — `id`, `tenant_id`, `name`, `color`, `order`, `type` (`lead` | `deal`).
- **leads** — `id`, `tenant_id`, `first_name`, `last_name`, `email`, `phone`, `company`, `stage_id`, `owner_id`, `source`, `created_at`.
- **deals** — `id`, `tenant_id`, `lead_id` (FK → leads), `title`, `value`, `currency`, `stage_id`, `probability`, `expected_close_date`.
- **activities** — `id`, `tenant_id`, `lead_id`, `deal_id`, `type` (`note` | `task` | `email`), `content` (jsonb), `created_by`, `created_at`.
- **tasks** — `id`, `tenant_id`, `lead_id`, `deal_id`, `title`, `due_date`, `assignee_id`, `status` (`open` | `done`).
- **custom_views** — `id`, `tenant_id`, `user_id`, `name`, `filters` (jsonb), `sort`, `columns`, `is_shared`.

### HR
- **employees** — `id`, `tenant_id`, `user_id` (FK → users), `department_id`, `manager_id` (self-FK), `designation`, `start_date`, `status` (`active` | `inactive`).
- **departments** — `id`, `tenant_id`, `name`, `head_id` (FK → employees).
- **attendance** — `id`, `tenant_id`, `employee_id`, `date`, `check_in`, `check_out`, `status` (`present` | `absent`), `half_day`, `holiday`.
- **leave_types** — `id`, `tenant_id`, `name`, `days_allowed`, `is_paid`, `carry_forward`.
- **leave_requests** — `id`, `tenant_id`, `employee_id`, `leave_type_id`, `start_date`, `end_date`, `reason`, `approved_by`, `status` (`pending` | `approved` | `rejected`).
- **leave_balances** — `id`, `tenant_id`, `employee_id`, `leave_type_id`, `year`, `total`, `used`, `remaining`.

---

## 5. CRM Module — Features & UI

### 5.1 Kanban Board (main dashboard)
- Columns are tenant-customizable `pipeline_stages` (e.g., New → Contacted → Qualified → Proposal → Won), each with a name, color, and order.
- Drag-and-drop cards between columns updates `stage_id`; moves broadcast in real time to other users.
- Cards show company, primary contact, owner avatar, and (for deals) value.
- Toggle between **Kanban** and **List** views.
- Top bar: New Lead, Filters, My Views selector.

### 5.2 Lead / Deal Detail Page
- Split layout: main content (left) + context sidebar (right).
- **Header:** name, title/company, "Convert to Deal" action, Edit.
- **Stage pills:** clickable progression showing current/past/next stages.
- **Activity tabs:** Activity (unified feed) · Tasks · Notes · Emails.
- **Activity feed:** chronological entries (notes added, stage changes, tasks, emails) with author avatars and timestamps; inline "Add a note" composer.
- **Right sidebar:** Contact Details (email, phone, company, location), Assigned To, Tasks checklist.

### 5.3 Custom Views & Filters
- **Filter builder:** stackable rows of `field` + `operator` + `value`; add/remove filters.
- **Saved views:** named, persisted to `custom_views`; each is **private** by default or **shared** with the team (`is_shared`).
- Views store filters, sort, and visible columns.

---

## 6. HR Module — Features & UI

### 6.1 HR Dashboard
- Stat cards: total employees, present today, on leave, pending requests (with trend/sub-text).
- **Employee directory:** searchable cards with avatar, department, designation, and live presence dot.

### 6.2 Org Chart
- Visual reporting hierarchy derived from `employees.manager_id`, rendered top-down from the org head through department heads to reports.

### 6.3 Attendance
- Contribution-grid ("GitHub-style") calendar of daily states: present, half-day, leave, absent, weekend/holiday.
- **Check In / Check Out** action recording `check_in` / `check_out` timestamps.

### 6.4 Leave Management
- Per-employee **leave balance bars** by leave type (used / total).
- **Request leave** flow (type, date range, reason).
- **Manager approval queue:** pending requests with inline approve/reject; updates `status`, `approved_by`, and recomputes `leave_balances`.

---

## 7. UI / Design System — "Midnight Signal"

The immersive UI is a primary requirement, informed by the frontend-design skill (distinctive, production-grade, anti-generic). For this data-dense productivity tool we apply the skill's craft while keeping `DESIGN_VARIANCE` moderate and `VISUAL_DENSITY` higher so screens stay scannable.

### Design Language: Midnight Signal
- **Canvas:** deep forest-ink (`#0a0f0e` → `#1b2e2a` gradient mesh).
- **Accent:** electric lime (`#c6f24e`) — single dominant accent with sharp contrast.
- **Text:** off-white (`#f4f6f4`), muted (`#8a958f`).
- **Surfaces:** glass panels (translucent + backdrop blur), layered depth, soft shadows.
- **Typography:** **Space Grotesk** (display/headings) + **Outfit** (body). No Inter/Roboto/Arial.
- **Icons:** Phosphor.
- **Theming:** token-driven via CSS variables; full **dark and light** themes from one source of truth.

### Immersive Interaction Requirements (all screens)
- **Orchestrated page load:** staggered reveal animations (cards fade/slide in in sequence), not simultaneous pop-in.
- **Physics-based drag:** Kanban cards lift, tilt, and spring-settle (Motion for Vue + vuedraggable).
- **Micro-interactions:** hover lifts, press states, animated number counters, toast notifications.
- **Atmosphere:** gradient-mesh headers, layered transparency, subtle grain/noise.
- **Skeleton loaders:** shimmer placeholders during data fetch — never blank screens.
- **Responsive:** mobile-first; inputs ≥16px to avoid mobile zoom; `min-h-[100dvh]` over `h-screen`.
- **Performance guardrails:** constrain blur/animation cost; respect `prefers-reduced-motion`.

---

## 8. Authentication & Authorization

- **Methods:** email + password, and Google OAuth.
- **Tokens:** JWT access + refresh; claims carry `user_id`, `tenant_id`, `role`.
- **Roles (initial):** at minimum `admin` and `member`; HR approvals gated to managers/admins. Role model refined during planning.
- **Tenant onboarding:** a sign-up creates a tenant + its first admin user; admins invite teammates.

---

## 9. Multi-Tenancy & Security

- Single shared PostgreSQL database; isolation via **Row-Level Security** keyed on `tenant_id`.
- Per-request tenant context set from the JWT by FastAPI middleware before any query runs.
- RLS policy on every tenant-scoped table: `tenant_id = current_setting('app.tenant_id')`.
- Passwords hashed with bcrypt; secrets via environment variables; HTTPS enforced by hosting providers.

---

## 10. Real-Time

- FastAPI WebSocket endpoint; clients join a **per-tenant room** on connect (authenticated via JWT).
- Broadcast events: Kanban stage moves, activity-feed additions, leave-request status changes.
- Frontend updates Pinia stores on receipt; optimistic UI for drag operations with server reconciliation.

---

## 11. Build Order

1. **Phase 0 — Foundation:** project scaffold (FE/BE), database + RLS, auth (email/password + Google OAuth), tenant onboarding, design-system tokens & shared components, app shell.
2. **Phase 1 — CRM:** pipeline stages, leads/deals, Kanban board (drag + real-time), lead/deal detail page, activities/tasks/notes, custom views & filters.
3. **Phase 2 — HR:** employees + departments, org chart, attendance, leave types/requests/balances + approvals.
4. **Later (deferred):** WhatsApp integration; billing/subscription tiers if pursued.

Each phase gets its own implementation plan via the writing-plans skill.

---

## 12. Open Questions for Planning

- Exact role/permission matrix (who can edit pipeline stages, share views, approve leave).
- Email delivery provider for OAuth/invites/notifications (free-tier option to select).
- Whether "Convert to Deal" copies the lead or links to it (current model: `deals.lead_id` links).
- Background-worker mechanism on Render free tier (in-process tasks vs. external queue).
