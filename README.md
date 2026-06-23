# CRM + HR Platform

Multi-tenant SaaS combining a sales CRM and a mid-range HR system.
FastAPI + Vue 3, PostgreSQL with Row-Level Security.

## Local development

### Backend
1. Create a Postgres DB and a **non-superuser** app role (see `backend/.env.example`).
2. `cd backend && pip install -e ".[dev]"`
3. Copy `.env.example` to `.env` and fill values.
4. `alembic upgrade head`
5. `uvicorn app.main:app --reload`
6. Tests: `pytest -v` (requires `TEST_DATABASE_URL` migrated, connected as the app role).

### Frontend
1. `cd frontend && npm install`
2. Copy `.env.example` to `.env`.
3. `npm run dev` → http://localhost:5173
4. Tests: `npm run test`

## Deployment (free tier)
- **DB:** Neon (create database + app role; run `alembic upgrade head`).
- **Backend:** Render (uses `backend/render.yaml`).
- **Frontend:** Vercel (uses `frontend/vercel.json`; set `VITE_API_URL` to the Render URL).

## Phases
- **Phase 0 (this):** auth, multi-tenancy, app shell, design system.
- **Phase 1:** CRM (Kanban, lead/deal detail, custom views).
- **Phase 2:** HR (directory, org chart, attendance, leave).
