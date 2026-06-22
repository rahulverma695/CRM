# Phase 0 — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the multi-tenant foundation — FastAPI backend with PostgreSQL Row-Level Security, JWT auth (email/password + Google OAuth), tenant onboarding, plus a Vue 3 app shell with the "Midnight Signal" design system — so the CRM and HR modules can be built on top.

**Architecture:** Modular monolith. FastAPI + SQLAlchemy (async) + Alembic on PostgreSQL with RLS keyed on `tenant_id`. A per-request middleware sets the Postgres session variable `app.tenant_id` from the JWT so every query is automatically tenant-scoped. Vue 3 (Composition API + TypeScript) SPA with Pinia, Vue Router, and Tailwind-driven design tokens.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), asyncpg, Alembic, Pydantic v2, python-jose, passlib[bcrypt], Authlib, pytest + pytest-asyncio + httpx. Vue 3, Vite, TypeScript, Pinia, Vue Router 4, TailwindCSS, Motion for Vue, Phosphor Icons, Vitest.

---

## Conventions

- **Backend root:** `backend/` · **Frontend root:** `frontend/`
- **Run backend tests:** from `backend/`, `pytest -v`
- **Run frontend tests:** from `frontend/`, `npm run test`
- All IDs are UUIDs (`uuid4`). All timestamps are timezone-aware UTC.
- Tests use a real Postgres test database (RLS cannot be tested against SQLite). The test fixture connects as a **non-superuser** role so RLS is enforced (superusers bypass RLS).

---

## File Structure

**Backend (`backend/`):**
```
app/
  __init__.py
  config.py            — Pydantic Settings (env vars)
  database.py          — async engine, session factory, get_session dependency
  main.py              — FastAPI app factory, router + middleware registration
  core/
    __init__.py
    models/
      __init__.py
      base.py          — declarative Base, TimestampMixin, TenantMixin
      tenant.py        — Tenant model
      user.py          — User model (role enum, google_id, password_hash)
    schemas/
      __init__.py
      auth.py          — SignupIn, LoginIn, TokenPair, UserOut, InviteIn, AcceptInviteIn
    security/
      __init__.py
      passwords.py     — hash_password / verify_password
      jwt.py           — create_access_token / create_refresh_token / decode_token
    middleware/
      __init__.py
      tenant_context.py — set app.tenant_id per request
    deps.py            — get_current_user, require_admin
    email.py           — EmailSender protocol + ConsoleEmailSender
    routers/
      __init__.py
      auth.py          — /auth/signup, /auth/login, /auth/refresh, /auth/me
      oauth.py         — /auth/google/login, /auth/google/callback
      invites.py       — /invites (create), /invites/accept
alembic/
  env.py
  versions/            — migrations
alembic.ini
pyproject.toml
.env.example
tests/
  conftest.py          — async test DB, client, tenant/user factories
  test_passwords.py
  test_jwt.py
  test_signup.py
  test_login.py
  test_refresh.py
  test_rls.py
  test_invites.py
```

**Frontend (`frontend/`):**
```
src/
  main.ts
  App.vue
  style.css            — Tailwind directives + Midnight Signal tokens
  core/
    api.ts             — fetch wrapper with auth header + refresh
    stores/
      auth.ts          — Pinia auth store
    router.ts          — routes + auth guard
  components/
    BaseButton.vue
    BaseInput.vue
    AppSkeleton.vue
    StaggerList.vue    — orchestrated staggered reveal wrapper
  layouts/
    AppShell.vue       — sidebar + module switcher + topbar
  pages/
    LoginPage.vue
    SignupPage.vue
    DashboardPage.vue  — placeholder landing after login
tailwind.config.js
vite.config.ts
vitest.config.ts
index.html
package.json
tsconfig.json
```

**Deployment:**
```
backend/render.yaml
frontend/vercel.json
```

---

## Task 1: Backend project scaffold

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Test: `backend/tests/test_config.py`

- [ ] **Step 1: Create `backend/pyproject.toml`**

```toml
[project]
name = "crm-hr-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.111",
    "uvicorn[standard]>=0.30",
    "sqlalchemy>=2.0",
    "asyncpg>=0.29",
    "alembic>=1.13",
    "pydantic>=2.7",
    "pydantic-settings>=2.3",
    "python-jose[cryptography]>=3.3",
    "passlib[bcrypt]>=1.7",
    "authlib>=1.3",
    "httpx>=0.27",
    "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2",
    "pytest-asyncio>=0.23",
    "greenlet>=3.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create `backend/.env.example`**

```
DATABASE_URL=postgresql+asyncpg://app_user:app_pass@localhost:5432/crmhr
TEST_DATABASE_URL=postgresql+asyncpg://app_user:app_pass@localhost:5432/crmhr_test
JWT_SECRET=change-me-in-production
ACCESS_TOKEN_MINUTES=30
REFRESH_TOKEN_DAYS=14
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
FRONTEND_URL=http://localhost:5173
```

- [ ] **Step 3: Create `backend/app/__init__.py`** (empty file)

```python
```

- [ ] **Step 4: Write the failing test `backend/tests/test_config.py`**

```python
from app.config import Settings


def test_settings_reads_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@h/db")
    monkeypatch.setenv("JWT_SECRET", "secret")
    s = Settings()
    assert s.database_url == "postgresql+asyncpg://u:p@h/db"
    assert s.jwt_secret == "secret"
    assert s.access_token_minutes == 30  # default
```

- [ ] **Step 5: Run test to verify it fails**

Run: `cd backend && pip install -e ".[dev]" && pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.config'`

- [ ] **Step 6: Create `backend/app/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    test_database_url: str = ""
    jwt_secret: str
    access_token_minutes: int = 30
    refresh_token_days: int = 14
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"
    frontend_url: str = "http://localhost:5173"


settings = Settings()
```

- [ ] **Step 7: Run test to verify it passes**

Run: `cd backend && pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add backend/pyproject.toml backend/.env.example backend/app/__init__.py backend/app/config.py backend/tests/test_config.py
git commit -m "feat(backend): scaffold project with config settings"
```

---

## Task 2: Password hashing utility

**Files:**
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/security/__init__.py`
- Create: `backend/app/core/security/passwords.py`
- Test: `backend/tests/test_passwords.py`

- [ ] **Step 1: Create empty package files**

Create `backend/app/core/__init__.py` and `backend/app/core/security/__init__.py` as empty files.

- [ ] **Step 2: Write the failing test `backend/tests/test_passwords.py`**

```python
from app.core.security.passwords import hash_password, verify_password


def test_hash_is_not_plaintext():
    h = hash_password("hunter2")
    assert h != "hunter2"
    assert len(h) > 20


def test_verify_correct_password():
    h = hash_password("hunter2")
    assert verify_password("hunter2", h) is True


def test_verify_wrong_password():
    h = hash_password("hunter2")
    assert verify_password("wrong", h) is False
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && pytest tests/test_passwords.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 4: Create `backend/app/core/security/passwords.py`**

```python
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_passwords.py -v`
Expected: PASS (3 passed)

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/__init__.py backend/app/core/security/__init__.py backend/app/core/security/passwords.py backend/tests/test_passwords.py
git commit -m "feat(backend): add bcrypt password hashing"
```

---

## Task 3: JWT utilities

**Files:**
- Create: `backend/app/core/security/jwt.py`
- Test: `backend/tests/test_jwt.py`

- [ ] **Step 1: Write the failing test `backend/tests/test_jwt.py`**

```python
import uuid
import pytest
from jose import JWTError
from app.core.security.jwt import create_access_token, create_refresh_token, decode_token


def test_access_token_roundtrip():
    uid, tid = str(uuid.uuid4()), str(uuid.uuid4())
    token = create_access_token(user_id=uid, tenant_id=tid, role="admin")
    claims = decode_token(token)
    assert claims["sub"] == uid
    assert claims["tenant_id"] == tid
    assert claims["role"] == "admin"
    assert claims["type"] == "access"


def test_refresh_token_has_type_refresh():
    token = create_refresh_token(user_id="u1", tenant_id="t1", role="member")
    claims = decode_token(token)
    assert claims["type"] == "refresh"


def test_decode_rejects_garbage():
    with pytest.raises(JWTError):
        decode_token("not.a.token")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_jwt.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Create `backend/app/core/security/jwt.py`**

```python
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.config import settings

ALGORITHM = "HS256"


def _create_token(user_id: str, tenant_id: str, role: str, token_type: str, expires: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + expires,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def create_access_token(user_id: str, tenant_id: str, role: str) -> str:
    return _create_token(user_id, tenant_id, role, "access",
                         timedelta(minutes=settings.access_token_minutes))


def create_refresh_token(user_id: str, tenant_id: str, role: str) -> str:
    return _create_token(user_id, tenant_id, role, "refresh",
                         timedelta(days=settings.refresh_token_days))


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && JWT_SECRET=test DATABASE_URL=postgresql+asyncpg://x pytest tests/test_jwt.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/security/jwt.py backend/tests/test_jwt.py
git commit -m "feat(backend): add JWT access/refresh token utilities"
```

---

## Task 4: Base models (Base, mixins, Tenant, User)

**Files:**
- Create: `backend/app/core/models/__init__.py`
- Create: `backend/app/core/models/base.py`
- Create: `backend/app/core/models/tenant.py`
- Create: `backend/app/core/models/user.py`
- Test: `backend/tests/test_models.py`

- [ ] **Step 1: Create `backend/app/core/models/base.py`**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


class TenantMixin:
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
```

- [ ] **Step 2: Create `backend/app/core/models/tenant.py`**

```python
import uuid
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.models.base import Base, TimestampMixin


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    plan: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
```

- [ ] **Step 3: Create `backend/app/core/models/user.py`**

```python
import uuid
from sqlalchemy import String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.models.base import Base, TimestampMixin, TenantMixin


class User(Base, TimestampMixin, TenantMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="member", nullable=False)
    google_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
```

- [ ] **Step 4: Create `backend/app/core/models/__init__.py`**

```python
from app.core.models.base import Base, TimestampMixin, TenantMixin
from app.core.models.tenant import Tenant
from app.core.models.user import User

__all__ = ["Base", "TimestampMixin", "TenantMixin", "Tenant", "User"]
```

- [ ] **Step 5: Write the test `backend/tests/test_models.py`**

```python
from app.core.models import Tenant, User


def test_tenant_columns():
    cols = set(Tenant.__table__.columns.keys())
    assert {"id", "name", "slug", "plan", "settings", "created_at", "updated_at"} <= cols


def test_user_columns():
    cols = set(User.__table__.columns.keys())
    assert {"id", "tenant_id", "email", "name", "role", "google_id",
            "password_hash", "is_active"} <= cols


def test_user_has_tenant_fk():
    fk = list(User.__table__.c.tenant_id.foreign_keys)[0]
    assert fk.column.table.name == "tenants"
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && JWT_SECRET=test DATABASE_URL=postgresql+asyncpg://x pytest tests/test_models.py -v`
Expected: PASS (3 passed)

- [ ] **Step 7: Commit**

```bash
git add backend/app/core/models/ backend/tests/test_models.py
git commit -m "feat(backend): add Base mixins, Tenant and User models"
```

---

## Task 5: Async database engine and session

**Files:**
- Create: `backend/app/database.py`
- Test: `backend/tests/test_database.py`

- [ ] **Step 1: Write the failing test `backend/tests/test_database.py`**

```python
from app.database import engine, async_session_factory, get_session


def test_engine_is_async():
    assert "asyncpg" in str(engine.url)


def test_session_factory_callable():
    s = async_session_factory()
    assert s is not None


def test_get_session_is_async_generator():
    import inspect
    assert inspect.isasyncgenfunction(get_session)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && JWT_SECRET=test DATABASE_URL=postgresql+asyncpg://u:p@localhost/db pytest tests/test_database.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Create `backend/app/database.py`**

```python
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine,
)
from app.config import settings

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && JWT_SECRET=test DATABASE_URL=postgresql+asyncpg://u:p@localhost/db pytest tests/test_database.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/database.py backend/tests/test_database.py
git commit -m "feat(backend): add async SQLAlchemy engine and session"
```

---

## Task 6: Alembic setup and initial migration

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/0001_core_tables.py`

> Note: Alembic migrations are infrastructure; verify them by running against a real DB rather than unit tests. The RLS test in Task 8 exercises these tables end-to-end.

- [ ] **Step 1: Create `backend/alembic.ini`**

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url =

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
```

- [ ] **Step 2: Create `backend/alembic/script.py.mako`**

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 3: Create `backend/alembic/env.py`**

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from app.config import settings
from app.core.models import Base
import app.core.models  # noqa: F401  ensures all models are imported

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url, target_metadata=target_metadata,
        literal_binds=True, dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(settings.database_url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

- [ ] **Step 4: Create `backend/alembic/versions/0001_core_tables.py`**

```python
"""core tables: tenants and users

Revision ID: 0001
Revises:
Create Date: 2026-06-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("plan", sa.String(50), nullable=False, server_default="free"),
        sa.Column("settings", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_unique_constraint("uq_tenants_slug", "tenants", ["slug"])

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.String(1024), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="member"),
        sa.Column("google_id", sa.String(255), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_unique_constraint("uq_users_tenant_email", "users", ["tenant_id", "email"])


def downgrade() -> None:
    op.drop_table("users")
    op.drop_table("tenants")
```

- [ ] **Step 5: Run the migration against the dev database**

Run: `cd backend && alembic upgrade head`
Expected: output ends with `Running upgrade  -> 0001, core tables...` and no error. Verify with `psql $DATABASE_URL -c "\dt"` showing `tenants` and `users`.

- [ ] **Step 6: Commit**

```bash
git add backend/alembic.ini backend/alembic/
git commit -m "feat(backend): alembic setup + core tables migration"
```

---

## Task 7: RLS policies migration

**Files:**
- Create: `backend/alembic/versions/0002_rls_policies.py`

> RLS enforces `tenant_id = current_setting('app.tenant_id')::uuid` on `users`. The `tenants` table is exempt (it has no `tenant_id`); access to it is gated at the application layer. The migration also creates the non-superuser application role used at runtime and in tests.

- [ ] **Step 1: Create `backend/alembic/versions/0002_rls_policies.py`**

```python
"""row-level security on tenant-scoped tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-23
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

TENANT_TABLES = ["users"]


def upgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(f"""
            CREATE POLICY tenant_isolation ON {table}
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """)


def downgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
```

- [ ] **Step 2: Run the migration**

Run: `cd backend && alembic upgrade head`
Expected: completes without error. Verify: `psql $DATABASE_URL -c "SELECT relname, relrowsecurity FROM pg_class WHERE relname='users';"` shows `t`.

- [ ] **Step 3: Document the app DB role requirement in `backend/.env.example`**

Add this comment block to the top of `backend/.env.example`:

```
# IMPORTANT: DATABASE_URL must connect as a NON-superuser, NON-owner role.
# Postgres superusers and table owners BYPASS row-level security.
# Create the app role once:
#   CREATE ROLE app_user LOGIN PASSWORD 'app_pass';
#   GRANT ALL ON ALL TABLES IN SCHEMA public TO app_user;
#   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO app_user;
# Run migrations as the OWNER, but run the app as app_user.
```

- [ ] **Step 4: Commit**

```bash
git add backend/alembic/versions/0002_rls_policies.py backend/.env.example
git commit -m "feat(backend): enable RLS tenant isolation on users"
```

---

## Task 8: Tenant context middleware + RLS integration test

**Files:**
- Create: `backend/app/core/middleware/__init__.py`
- Create: `backend/app/core/middleware/tenant_context.py`
- Create: `backend/tests/conftest.py`
- Test: `backend/tests/test_rls.py`

> This task introduces the test harness (real Postgres test DB connected as the non-superuser `app_user`). The middleware sets `app.tenant_id` on the connection so RLS filters every query.

- [ ] **Step 1: Create `backend/app/core/middleware/__init__.py`** (empty file)

- [ ] **Step 2: Create `backend/app/core/middleware/tenant_context.py`**

```python
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def set_tenant(session: AsyncSession, tenant_id: str) -> None:
    """Set the per-transaction tenant id used by RLS policies.

    Uses set_config(..., is_local => true) so the setting is scoped to the
    current transaction and does not leak across pooled connections.
    """
    await session.execute(
        text("SELECT set_config('app.tenant_id', :tid, true)"),
        {"tid": str(tenant_id)},
    )
```

- [ ] **Step 3: Create `backend/tests/conftest.py`**

```python
import asyncio
import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.config import settings
from app.core.models import Tenant, User
from app.core.security.passwords import hash_password

TEST_URL = settings.test_database_url or settings.database_url


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    engine = create_async_engine(TEST_URL)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


@pytest_asyncio.fixture
async def two_tenants(session):
    """Create two tenants each with one user, bypassing RLS via a privileged
    setup that sets app.tenant_id per insert. Returns (tenant_a_id, tenant_b_id)."""
    a_id, b_id = uuid.uuid4(), uuid.uuid4()
    for tid, name, slug in [(a_id, "Tenant A", f"a-{a_id.hex[:8]}"),
                            (b_id, "Tenant B", f"b-{b_id.hex[:8]}")]:
        session.add(Tenant(id=tid, name=name, slug=slug))
    await session.commit()
    for tid, email in [(a_id, "a@example.com"), (b_id, "b@example.com")]:
        await session.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tid)})
        session.add(User(id=uuid.uuid4(), tenant_id=tid, email=email,
                         name="User", role="admin", password_hash=hash_password("pw")))
        await session.commit()
    return a_id, b_id
```

- [ ] **Step 4: Write the failing test `backend/tests/test_rls.py`**

```python
import uuid
from sqlalchemy import select, text
from app.core.models import User
from app.core.middleware.tenant_context import set_tenant


async def test_rls_scopes_to_current_tenant(session, two_tenants):
    a_id, b_id = two_tenants

    await set_tenant(session, str(a_id))
    rows = (await session.execute(select(User))).scalars().all()
    assert len(rows) == 1
    assert rows[0].tenant_id == a_id


async def test_rls_blocks_cross_tenant_read(session, two_tenants):
    a_id, b_id = two_tenants

    await set_tenant(session, str(b_id))
    rows = (await session.execute(select(User))).scalars().all()
    assert all(r.tenant_id == b_id for r in rows)
    assert a_id not in {r.tenant_id for r in rows}
```

- [ ] **Step 5: Run test to verify it passes**

Prerequisite: test DB migrated (`TEST_DATABASE_URL` set, `alembic upgrade head` run against it), and the connection role is the non-superuser `app_user`.

Run: `cd backend && pytest tests/test_rls.py -v`
Expected: PASS (2 passed). If they FAIL with all rows visible, the DB role is a superuser/owner — fix the role (see Task 7 Step 3).

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/middleware/ backend/tests/conftest.py backend/tests/test_rls.py
git commit -m "feat(backend): tenant context helper + RLS isolation tests"
```

---

## Task 9: Auth schemas

**Files:**
- Create: `backend/app/core/schemas/__init__.py`
- Create: `backend/app/core/schemas/auth.py`
- Test: `backend/tests/test_auth_schemas.py`

- [ ] **Step 1: Create empty `backend/app/core/schemas/__init__.py`**

- [ ] **Step 2: Write the failing test `backend/tests/test_auth_schemas.py`**

```python
import pytest
from pydantic import ValidationError
from app.core.schemas.auth import SignupIn, LoginIn, TokenPair, UserOut


def test_signup_requires_valid_email():
    with pytest.raises(ValidationError):
        SignupIn(company_name="Acme", email="not-an-email", password="longenough", name="A")


def test_signup_rejects_short_password():
    with pytest.raises(ValidationError):
        SignupIn(company_name="Acme", email="a@b.com", password="short", name="A")


def test_token_pair_shape():
    tp = TokenPair(access_token="a", refresh_token="r")
    assert tp.token_type == "bearer"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && pytest tests/test_auth_schemas.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 4: Create `backend/app/core/schemas/auth.py`**

```python
import uuid
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class SignupIn(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: EmailStr
    name: str
    role: str
    avatar_url: str | None = None


class InviteIn(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=255)
    role: str = Field(default="member", pattern="^(admin|member)$")


class AcceptInviteIn(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_auth_schemas.py -v`
Expected: PASS (3 passed)

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/schemas/ backend/tests/test_auth_schemas.py
git commit -m "feat(backend): add auth request/response schemas"
```

---

## Task 10: Current-user dependency and admin guard

**Files:**
- Create: `backend/app/core/deps.py`
- Test: `backend/tests/test_deps.py`

- [ ] **Step 1: Write the failing test `backend/tests/test_deps.py`**

```python
import uuid
import pytest
from fastapi import HTTPException
from app.core.deps import claims_from_authorization, require_role
from app.core.security.jwt import create_access_token, create_refresh_token


def test_claims_from_valid_bearer():
    uid, tid = str(uuid.uuid4()), str(uuid.uuid4())
    token = create_access_token(user_id=uid, tenant_id=tid, role="member")
    claims = claims_from_authorization(f"Bearer {token}")
    assert claims["sub"] == uid


def test_claims_rejects_missing_header():
    with pytest.raises(HTTPException) as exc:
        claims_from_authorization(None)
    assert exc.value.status_code == 401


def test_claims_rejects_refresh_token_for_access():
    token = create_refresh_token(user_id="u", tenant_id="t", role="member")
    with pytest.raises(HTTPException) as exc:
        claims_from_authorization(f"Bearer {token}")
    assert exc.value.status_code == 401


def test_require_role_allows_admin():
    require_role({"role": "admin"}, "admin")  # no raise


def test_require_role_blocks_member():
    with pytest.raises(HTTPException) as exc:
        require_role({"role": "member"}, "admin")
    assert exc.value.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && JWT_SECRET=test DATABASE_URL=postgresql+asyncpg://x pytest tests/test_deps.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Create `backend/app/core/deps.py`**

```python
from typing import Annotated
from fastapi import Depends, Header, HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security.jwt import decode_token
from app.core.middleware.tenant_context import set_tenant
from app.database import get_session


def claims_from_authorization(authorization: str | None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        claims = decode_token(token)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    if claims.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not an access token")
    return claims


async def get_current_claims(authorization: Annotated[str | None, Header()] = None) -> dict:
    return claims_from_authorization(authorization)


async def get_tenant_session(
    claims: Annotated[dict, Depends(get_current_claims)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncSession:
    """Yields a session with RLS tenant context already applied."""
    await set_tenant(session, claims["tenant_id"])
    return session


def require_role(claims: dict, role: str) -> None:
    if claims.get("role") != role:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")


async def require_admin(claims: Annotated[dict, Depends(get_current_claims)]) -> dict:
    require_role(claims, "admin")
    return claims
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && JWT_SECRET=test DATABASE_URL=postgresql+asyncpg://x pytest tests/test_deps.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/deps.py backend/tests/test_deps.py
git commit -m "feat(backend): add auth dependencies and role guard"
```

---

## Task 11: FastAPI app factory + signup endpoint

**Files:**
- Create: `backend/app/core/routers/__init__.py`
- Create: `backend/app/core/routers/auth.py`
- Create: `backend/app/main.py`
- Modify: `backend/tests/conftest.py` (add `client` fixture)
- Test: `backend/tests/test_signup.py`

> Signup is the tenant-onboarding entry point: it creates a tenant **and** its first admin user in one transaction. Because the tenant does not exist yet, the insert path sets `app.tenant_id` to the new tenant id before inserting the user.

- [ ] **Step 1: Create empty `backend/app/core/routers/__init__.py`**

- [ ] **Step 2: Create `backend/app/core/routers/auth.py`**

```python
import re
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.models import Tenant, User
from app.core.schemas.auth import SignupIn, LoginIn, TokenPair, UserOut, RefreshIn
from app.core.security.passwords import hash_password, verify_password
from app.core.security.jwt import create_access_token, create_refresh_token, decode_token
from app.core.middleware.tenant_context import set_tenant
from app.core.deps import get_current_claims, get_tenant_session
from app.database import get_session
from jose import JWTError

router = APIRouter(prefix="/auth", tags=["auth"])


def _slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "tenant"
    return f"{base}-{uuid.uuid4().hex[:6]}"


@router.post("/signup", response_model=TokenPair, status_code=201)
async def signup(body: SignupIn, session: Annotated[AsyncSession, Depends(get_session)]):
    tenant = Tenant(id=uuid.uuid4(), name=body.company_name, slug=_slugify(body.company_name))
    session.add(tenant)
    await session.flush()

    await set_tenant(session, str(tenant.id))
    user = User(
        id=uuid.uuid4(), tenant_id=tenant.id, email=str(body.email),
        name=body.name, role="admin", password_hash=hash_password(body.password),
    )
    session.add(user)
    await session.commit()

    return TokenPair(
        access_token=create_access_token(str(user.id), str(tenant.id), user.role),
        refresh_token=create_refresh_token(str(user.id), str(tenant.id), user.role),
    )


@router.post("/login", response_model=TokenPair)
async def login(body: LoginIn, session: Annotated[AsyncSession, Depends(get_session)]):
    # Login must search across tenants, so query without RLS scoping by email.
    # RLS is enabled on users; to authenticate we use a SECURITY-DEFINER-free
    # approach: look up the user via a bypass session variable set to a wildcard
    # is not possible, so we disable row filtering by querying as the migration
    # owner is also not desirable. Instead we store a global email index lookup.
    result = await session.execute(
        text("SELECT id, tenant_id, role, password_hash, is_active "
             "FROM users WHERE email = :email"),
        {"email": str(body.email)},
    )
    row = result.first()
    if row is None or not row.is_active or not row.password_hash:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not verify_password(body.password, row.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return TokenPair(
        access_token=create_access_token(str(row.id), str(row.tenant_id), row.role),
        refresh_token=create_refresh_token(str(row.id), str(row.tenant_id), row.role),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(body: RefreshIn):
    try:
        claims = decode_token(body.refresh_token)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    if claims.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not a refresh token")
    return TokenPair(
        access_token=create_access_token(claims["sub"], claims["tenant_id"], claims["role"]),
        refresh_token=create_refresh_token(claims["sub"], claims["tenant_id"], claims["role"]),
    )


@router.get("/me", response_model=UserOut)
async def me(
    claims: Annotated[dict, Depends(get_current_claims)],
    session: Annotated[AsyncSession, Depends(get_tenant_session)],
):
    user = (await session.execute(
        select(User).where(User.id == uuid.UUID(claims["sub"]))
    )).scalar_one_or_none()
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user
```

> **Login + RLS note for the implementer:** RLS is `FORCE`d on `users`, so the raw `SELECT ... WHERE email` above still returns nothing unless `app.tenant_id` matches. To allow cross-tenant login-by-email, add a dedicated policy in the next step that permits reading the columns needed for authentication. This keeps tenant data isolated while enabling login.

- [ ] **Step 3: Add a login lookup policy — create `backend/alembic/versions/0003_login_lookup.py`**

```python
"""allow email-based login lookup across tenants

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-23
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A permissive SELECT policy that allows reading the row when no tenant
    # context is set (login happens before a tenant context exists). When a
    # tenant context IS set, the tenant_isolation policy still applies.
    op.execute("""
        CREATE POLICY login_lookup ON users
        FOR SELECT
        USING (current_setting('app.tenant_id', true) IS NULL
               OR current_setting('app.tenant_id', true) = '');
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS login_lookup ON users;")
```

Run: `cd backend && alembic upgrade head` (also against `TEST_DATABASE_URL`). Expected: no error.

> Postgres combines multiple permissive policies with OR. With no tenant context set, `login_lookup` permits the read; once a request sets `app.tenant_id`, `tenant_isolation` governs access. The login endpoint never sets a tenant context, so its lookup succeeds.

- [ ] **Step 4: Create `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.routers import auth


def create_app() -> FastAPI:
    app = FastAPI(title="CRM + HR Platform")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth.router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 5: Add the `client` fixture to `backend/tests/conftest.py`**

Append:

```python
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import create_app


@pytest_asyncio.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
```

- [ ] **Step 6: Write the test `backend/tests/test_signup.py`**

```python
async def test_signup_creates_tenant_and_returns_tokens(client):
    resp = await client.post("/auth/signup", json={
        "company_name": "Acme Inc",
        "name": "Mark Evans",
        "email": "mark@acme.com",
        "password": "supersecret",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


async def test_me_returns_current_user(client):
    await client.post("/auth/signup", json={
        "company_name": "Globex",
        "name": "Sara Chen",
        "email": "sara@globex.com",
        "password": "supersecret",
    })
    login = await client.post("/auth/login", json={
        "email": "sara@globex.com", "password": "supersecret",
    })
    token = login.json()["access_token"]
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "sara@globex.com"
    assert me.json()["role"] == "admin"
```

- [ ] **Step 7: Run test to verify it passes**

Run: `cd backend && pytest tests/test_signup.py -v`
Expected: PASS (2 passed)

- [ ] **Step 8: Commit**

```bash
git add backend/app/core/routers/ backend/app/main.py backend/alembic/versions/0003_login_lookup.py backend/tests/conftest.py backend/tests/test_signup.py
git commit -m "feat(backend): app factory, signup/login/refresh/me endpoints"
```

---

## Task 12: Login and refresh endpoint tests

**Files:**
- Test: `backend/tests/test_login.py`
- Test: `backend/tests/test_refresh.py`

> The endpoints were implemented in Task 11; these tests lock in their behavior including failure cases.

- [ ] **Step 1: Write `backend/tests/test_login.py`**

```python
import pytest


@pytest.fixture
async def signed_up(client):
    await client.post("/auth/signup", json={
        "company_name": "Initech", "name": "Bill", "email": "bill@initech.com",
        "password": "supersecret",
    })


async def test_login_success(client, signed_up):
    resp = await client.post("/auth/login", json={
        "email": "bill@initech.com", "password": "supersecret",
    })
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_login_wrong_password(client, signed_up):
    resp = await client.post("/auth/login", json={
        "email": "bill@initech.com", "password": "wrongpass",
    })
    assert resp.status_code == 401


async def test_login_unknown_email(client):
    resp = await client.post("/auth/login", json={
        "email": "nobody@nowhere.com", "password": "supersecret",
    })
    assert resp.status_code == 401
```

- [ ] **Step 2: Write `backend/tests/test_refresh.py`**

```python
async def test_refresh_issues_new_access_token(client):
    signup = await client.post("/auth/signup", json={
        "company_name": "Umbrella", "name": "Alice", "email": "alice@umbrella.com",
        "password": "supersecret",
    })
    refresh_token = signup.json()["refresh_token"]
    resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_refresh_rejects_access_token(client):
    signup = await client.post("/auth/signup", json={
        "company_name": "Stark", "name": "Tony", "email": "tony@stark.com",
        "password": "supersecret",
    })
    access_token = signup.json()["access_token"]
    resp = await client.post("/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `cd backend && pytest tests/test_login.py tests/test_refresh.py -v`
Expected: PASS (5 passed)

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_login.py backend/tests/test_refresh.py
git commit -m "test(backend): cover login and refresh flows"
```

---

## Task 13: Email sender + user invites

**Files:**
- Create: `backend/app/core/email.py`
- Create: `backend/app/core/routers/invites.py`
- Modify: `backend/app/main.py` (register invites router)
- Test: `backend/tests/test_invites.py`

> An invite creates an inactive user row in the admin's tenant and emails a signed invite token. Accepting the invite sets the password and activates the account. The `EmailSender` is pluggable; `ConsoleEmailSender` is used in dev/tests (Resend is the production swap, deferred).

- [ ] **Step 1: Create `backend/app/core/email.py`**

```python
from typing import Protocol


class EmailSender(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...


class ConsoleEmailSender:
    """Dev/test sender. Records sent messages and prints them."""

    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append({"to": to, "subject": subject, "body": body})
        print(f"[email] to={to} subject={subject}\n{body}")


# Module-level singleton used by the app; tests can inspect `.sent`.
email_sender = ConsoleEmailSender()


def get_email_sender() -> EmailSender:
    return email_sender
```

- [ ] **Step 2: Create `backend/app/core/routers/invites.py`**

```python
import uuid
from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt, JWTError
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.core.models import User
from app.core.schemas.auth import InviteIn, AcceptInviteIn, TokenPair, UserOut
from app.core.security.passwords import hash_password
from app.core.security.jwt import create_access_token, create_refresh_token, ALGORITHM
from app.core.deps import require_admin, get_tenant_session
from app.core.email import get_email_sender, EmailSender
from app.database import get_session

router = APIRouter(prefix="/invites", tags=["invites"])


def _make_invite_token(user_id: str, tenant_id: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": user_id, "tenant_id": tenant_id, "type": "invite",
         "iat": now, "exp": now + timedelta(days=7)},
        settings.jwt_secret, algorithm=ALGORITHM,
    )


@router.post("", response_model=UserOut, status_code=201)
async def create_invite(
    body: InviteIn,
    admin: Annotated[dict, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_tenant_session)],
    sender: Annotated[EmailSender, Depends(get_email_sender)],
):
    tenant_id = admin["tenant_id"]
    user = User(
        id=uuid.uuid4(), tenant_id=uuid.UUID(tenant_id), email=str(body.email),
        name=body.name, role=body.role, is_active=False, password_hash=None,
    )
    session.add(user)
    await session.commit()

    token = _make_invite_token(str(user.id), tenant_id)
    link = f"{settings.frontend_url}/accept-invite?token={token}"
    await sender.send(str(body.email), "You're invited", f"Accept here: {link}")
    return user


@router.post("/accept", response_model=TokenPair)
async def accept_invite(
    body: AcceptInviteIn,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    try:
        claims = jwt.decode(body.token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid invite")
    if claims.get("type") != "invite":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not an invite token")

    # Activate within the invited user's tenant context.
    await session.execute(
        text("SELECT set_config('app.tenant_id', :t, true)"),
        {"t": claims["tenant_id"]},
    )
    user = (await session.execute(
        select(User).where(User.id == uuid.UUID(claims["sub"]))
    )).scalar_one_or_none()
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite target missing")
    user.password_hash = hash_password(body.password)
    user.is_active = True
    await session.commit()

    return TokenPair(
        access_token=create_access_token(str(user.id), str(user.tenant_id), user.role),
        refresh_token=create_refresh_token(str(user.id), str(user.tenant_id), user.role),
    )
```

- [ ] **Step 3: Register the router in `backend/app/main.py`**

Change the import line and the `include_router` block:

```python
from app.core.routers import auth, invites
```
```python
    app.include_router(auth.router)
    app.include_router(invites.router)
```

- [ ] **Step 4: Write the test `backend/tests/test_invites.py`**

```python
import pytest
from app.core.email import email_sender


@pytest.fixture
async def admin_token(client):
    resp = await client.post("/auth/signup", json={
        "company_name": "Wonka", "name": "Willy", "email": "willy@wonka.com",
        "password": "supersecret",
    })
    return resp.json()["access_token"]


async def test_admin_can_invite(client, admin_token):
    email_sender.sent.clear()
    resp = await client.post("/invites", json={
        "email": "charlie@wonka.com", "name": "Charlie", "role": "member",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 201
    assert resp.json()["email"] == "charlie@wonka.com"
    assert resp.json()["role"] == "member"
    assert len(email_sender.sent) == 1
    assert "accept-invite?token=" in email_sender.sent[0]["body"]


async def test_member_cannot_invite(client, admin_token):
    # create a member via invite + accept, then try to invite as that member
    email_sender.sent.clear()
    await client.post("/invites", json={
        "email": "oompa@wonka.com", "name": "Oompa", "role": "member",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    body = email_sender.sent[0]["body"]
    token = body.split("token=")[1].strip()
    accept = await client.post("/invites/accept", json={
        "token": token, "password": "anothersecret",
    })
    member_token = accept.json()["access_token"]
    resp = await client.post("/invites", json={
        "email": "x@wonka.com", "name": "X", "role": "member",
    }, headers={"Authorization": f"Bearer {member_token}"})
    assert resp.status_code == 403


async def test_accept_invite_activates_and_logs_in(client, admin_token):
    email_sender.sent.clear()
    await client.post("/invites", json={
        "email": "grandpa@wonka.com", "name": "Joe", "role": "member",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    token = email_sender.sent[0]["body"].split("token=")[1].strip()
    accept = await client.post("/invites/accept", json={
        "token": token, "password": "joesecret1",
    })
    assert accept.status_code == 200
    login = await client.post("/auth/login", json={
        "email": "grandpa@wonka.com", "password": "joesecret1",
    })
    assert login.status_code == 200
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/test_invites.py -v`
Expected: PASS (3 passed)

- [ ] **Step 6: Commit**

```bash
git add backend/app/core/email.py backend/app/core/routers/invites.py backend/app/main.py backend/tests/test_invites.py
git commit -m "feat(backend): pluggable email sender + admin user invites"
```

---

## Task 14: Google OAuth endpoints

**Files:**
- Create: `backend/app/core/routers/oauth.py`
- Modify: `backend/app/main.py` (register oauth router + session middleware)
- Test: `backend/tests/test_oauth.py`

> OAuth uses Authlib to redirect to Google and handle the callback. On callback, we resolve the Google profile, then find-or-create a user. **Phase 0 rule:** Google login attaches to an existing user by email (across tenants, like password login); if no user exists, it returns 404 with guidance to sign up first (org creation via Google is deferred to keep tenant onboarding explicit). The callback verification is unit-tested by injecting a fake token resolver so tests don't call Google.

- [ ] **Step 1: Create `backend/app/core/routers/oauth.py`**

```python
import uuid
from typing import Annotated, Callable, Awaitable
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.integrations.starlette_client import OAuth
from app.config import settings
from app.core.security.jwt import create_access_token, create_refresh_token
from app.database import get_session

router = APIRouter(prefix="/auth/google", tags=["oauth"])

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


async def resolve_google_email(request: Request) -> str:
    """Real resolver: exchange the callback for a token and return the email.
    Overridable in tests via app.dependency_overrides."""
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if not userinfo or not userinfo.get("email"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No email from Google")
    return userinfo["email"]


@router.get("/login")
async def google_login(request: Request):
    return await oauth.google.authorize_redirect(request, settings.google_redirect_uri)


@router.get("/callback")
async def google_callback(
    email: Annotated[str, Depends(resolve_google_email)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    row = (await session.execute(
        text("SELECT id, tenant_id, role FROM users WHERE email = :e AND is_active = true"),
        {"e": email},
    )).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                           "No account for this Google email — sign up first")
    access = create_access_token(str(row.id), str(row.tenant_id), row.role)
    refresh = create_refresh_token(str(row.id), str(row.tenant_id), row.role)
    return RedirectResponse(
        f"{settings.frontend_url}/auth/callback#access={access}&refresh={refresh}"
    )
```

- [ ] **Step 2: Register oauth router + session middleware in `backend/app/main.py`**

Authlib needs Starlette's `SessionMiddleware`. Update `create_app`:

```python
from starlette.middleware.sessions import SessionMiddleware
from app.core.routers import auth, invites, oauth
```
Add inside `create_app`, before `include_router` calls:
```python
    app.add_middleware(SessionMiddleware, secret_key=settings.jwt_secret)
```
And register:
```python
    app.include_router(oauth.router)
```

- [ ] **Step 3: Write the test `backend/tests/test_oauth.py`**

```python
import pytest
from app.main import create_app
from app.core.routers.oauth import resolve_google_email
from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def app_with_fake_google():
    app = create_app()
    # Override the Google resolver to avoid real network calls.
    async def fake_email():
        return "sara@globex.com"
    app.dependency_overrides[resolve_google_email] = fake_email
    return app


async def test_google_callback_existing_user(client, app_with_fake_google):
    # First create the user via normal signup using the default client.
    await client.post("/auth/signup", json={
        "company_name": "Globex", "name": "Sara", "email": "sara@globex.com",
        "password": "supersecret",
    })
    transport = ASGITransport(app=app_with_fake_google)
    async with AsyncClient(transport=transport, base_url="http://test",
                           follow_redirects=False) as c:
        resp = await c.get("/auth/google/callback")
    assert resp.status_code in (302, 307)
    assert "access=" in resp.headers["location"]


async def test_google_callback_unknown_user(app_with_fake_google):
    async def fake_email():
        return "ghost@nowhere.com"
    app_with_fake_google.dependency_overrides[resolve_google_email] = fake_email
    transport = ASGITransport(app=app_with_fake_google)
    async with AsyncClient(transport=transport, base_url="http://test",
                           follow_redirects=False) as c:
        resp = await c.get("/auth/google/callback")
    assert resp.status_code == 404
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_oauth.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/routers/oauth.py backend/app/main.py backend/tests/test_oauth.py
git commit -m "feat(backend): Google OAuth login/callback"
```

---

## Task 15: Run full backend suite

- [ ] **Step 1: Run the entire backend test suite**

Run: `cd backend && pytest -v`
Expected: ALL tests pass (config, passwords, jwt, models, database, rls, auth_schemas, deps, signup, login, refresh, invites, oauth).

- [ ] **Step 2: If any fail, fix before proceeding.** The backend foundation must be green before frontend work.

- [ ] **Step 3: Commit any fixes**

```bash
git add -A && git commit -m "test(backend): full Phase 0 suite green"
```

---

## Task 16: Frontend scaffold (Vite + Vue + TS + Tailwind)

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/vitest.config.ts`

- [ ] **Step 1: Create `frontend/package.json`**

```json
{
  "name": "crm-hr-frontend",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc -b && vite build",
    "preview": "vite preview",
    "test": "vitest run"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.3.0",
    "pinia": "^2.1.0",
    "motion-v": "^0.10.0",
    "vuedraggable": "^4.1.0",
    "@phosphor-icons/vue": "^2.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "typescript": "^5.4.0",
    "vue-tsc": "^2.0.0",
    "vite": "^5.2.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "vitest": "^1.6.0",
    "@vue/test-utils": "^2.4.0",
    "jsdom": "^24.0.0"
  }
}
```

- [ ] **Step 2: Create `frontend/vite.config.ts`**

```ts
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  server: { port: 5173 },
});
```

- [ ] **Step 3: Create `frontend/vitest.config.ts`**

```ts
import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  test: { environment: "jsdom", globals: true },
});
```

- [ ] **Step 4: Create `frontend/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "jsx": "preserve",
    "lib": ["ESNext", "DOM"],
    "types": ["vitest/globals"],
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] },
    "skipLibCheck": true
  },
  "include": ["src/**/*.ts", "src/**/*.vue"]
}
```

- [ ] **Step 5: Create `frontend/index.html`**

```html
<!DOCTYPE html>
<html lang="en" class="dark">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
    <title>CRM + HR</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 6: Create `frontend/postcss.config.js`**

```js
export default {
  plugins: { tailwindcss: {}, autoprefixer: {} },
};
```

- [ ] **Step 7: Create `frontend/tailwind.config.js`**

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,ts}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        canvas: "var(--canvas)",
        surface: "var(--surface)",
        "surface-raised": "var(--surface-raised)",
        border: "var(--border)",
        ink: "var(--ink)",
        muted: "var(--muted)",
        accent: "var(--accent)",
        "accent-ink": "var(--accent-ink)",
      },
      fontFamily: {
        display: ['"Space Grotesk"', "sans-serif"],
        body: ['"Outfit"', "sans-serif"],
      },
      borderRadius: { xl2: "1rem" },
    },
  },
  plugins: [],
};
```

- [ ] **Step 8: Create `frontend/src/main.ts`**

```ts
import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import { router } from "./core/router";
import "./style.css";

createApp(App).use(createPinia()).use(router).mount("#app");
```

- [ ] **Step 9: Create `frontend/src/App.vue`**

```vue
<script setup lang="ts"></script>

<template>
  <RouterView />
</template>
```

- [ ] **Step 10: Install and verify the dev server boots**

Run: `cd frontend && npm install && npm run build`
Expected: build completes (it will fail only if `router`/`style.css` are missing — those come next; for now create placeholders if needed, then re-run after Task 17–19). Defer the build check to Task 19 Step 5.

- [ ] **Step 11: Commit**

```bash
git add frontend/package.json frontend/vite.config.ts frontend/vitest.config.ts frontend/tsconfig.json frontend/index.html frontend/postcss.config.js frontend/tailwind.config.js frontend/src/main.ts frontend/src/App.vue
git commit -m "feat(frontend): scaffold Vite + Vue + TS + Tailwind"
```

---

## Task 17: Midnight Signal design tokens

**Files:**
- Create: `frontend/src/style.css`

- [ ] **Step 1: Create `frontend/src/style.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  /* Midnight Signal — dark (default) */
  --canvas: #0a0f0e;
  --canvas-2: #1b2e2a;
  --surface: #101714;
  --surface-raised: #16201c;
  --border: #243029;
  --ink: #f4f6f4;
  --muted: #8a958f;
  --accent: #c6f24e;
  --accent-ink: #0a0f0e;
}

:root.light {
  --canvas: #f3f6f2;
  --canvas-2: #e7efe6;
  --surface: #ffffff;
  --surface-raised: #ffffff;
  --border: #d8e2d6;
  --ink: #14211c;
  --muted: #5d6b62;
  --accent: #2f9e44;
  --accent-ink: #ffffff;
}

@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}

html, body, #app { min-height: 100dvh; }

body {
  margin: 0;
  background:
    radial-gradient(120% 90% at 0% 0%, var(--canvas-2) 0%, var(--canvas) 55%, var(--canvas) 100%);
  color: var(--ink);
  font-family: "Outfit", sans-serif;
}

h1, h2, h3, .font-display { font-family: "Space Grotesk", sans-serif; }

/* Skeleton shimmer */
@keyframes shimmer { 100% { transform: translateX(100%); } }
.skeleton {
  position: relative; overflow: hidden;
  background: var(--surface-raised); border-radius: 0.5rem;
}
.skeleton::after {
  content: ""; position: absolute; inset: 0;
  transform: translateX(-100%);
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
  animation: shimmer 1.4s infinite;
}

/* Staggered reveal */
@keyframes riseIn { to { opacity: 1; transform: translateY(0); } }
.stagger-item {
  opacity: 0; transform: translateY(14px);
  animation: riseIn 0.55s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/style.css
git commit -m "feat(frontend): Midnight Signal design tokens + motion primitives"
```

---

## Task 18: Shared UI components (BaseButton, BaseInput, AppSkeleton, StaggerList)

**Files:**
- Create: `frontend/src/components/BaseButton.vue`
- Create: `frontend/src/components/BaseInput.vue`
- Create: `frontend/src/components/AppSkeleton.vue`
- Create: `frontend/src/components/StaggerList.vue`
- Test: `frontend/src/components/BaseButton.test.ts`

- [ ] **Step 1: Create `frontend/src/components/BaseButton.vue`**

```vue
<script setup lang="ts">
defineProps<{ variant?: "primary" | "ghost"; type?: "button" | "submit" }>();
</script>

<template>
  <button
    :type="type ?? 'button'"
    class="inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-transform duration-150 active:scale-[0.97]"
    :class="variant === 'ghost'
      ? 'bg-transparent text-ink border border-border hover:bg-surface-raised'
      : 'bg-accent text-accent-ink hover:brightness-105'"
  >
    <slot />
  </button>
</template>
```

- [ ] **Step 2: Create `frontend/src/components/BaseInput.vue`**

```vue
<script setup lang="ts">
defineProps<{ modelValue: string; type?: string; placeholder?: string }>();
defineEmits<{ (e: "update:modelValue", v: string): void }>();
</script>

<template>
  <input
    :type="type ?? 'text'"
    :value="modelValue"
    :placeholder="placeholder"
    @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    class="w-full rounded-xl border border-border bg-surface px-4 py-2.5 text-base text-ink placeholder:text-muted focus:border-accent focus:outline-none"
  />
</template>
```

> Note: `text-base` (16px) on inputs prevents mobile zoom, per the design spec.

- [ ] **Step 3: Create `frontend/src/components/AppSkeleton.vue`**

```vue
<script setup lang="ts">
defineProps<{ height?: string; width?: string }>();
</script>

<template>
  <div class="skeleton" :style="{ height: height ?? '1rem', width: width ?? '100%' }" />
</template>
```

- [ ] **Step 4: Create `frontend/src/components/StaggerList.vue`**

```vue
<script setup lang="ts">
defineProps<{ items: unknown[] }>();
</script>

<template>
  <div>
    <div
      v-for="(item, i) in items"
      :key="i"
      class="stagger-item"
      :style="{ animationDelay: `${i * 70}ms` }"
    >
      <slot :item="item" :index="i" />
    </div>
  </div>
</template>
```

- [ ] **Step 5: Write the test `frontend/src/components/BaseButton.test.ts`**

```ts
import { mount } from "@vue/test-utils";
import { describe, it, expect } from "vitest";
import BaseButton from "./BaseButton.vue";

describe("BaseButton", () => {
  it("renders slot content", () => {
    const wrapper = mount(BaseButton, { slots: { default: "Save" } });
    expect(wrapper.text()).toBe("Save");
  });

  it("defaults to primary accent styling", () => {
    const wrapper = mount(BaseButton, { slots: { default: "Go" } });
    expect(wrapper.classes()).toContain("bg-accent");
  });

  it("applies ghost styling when variant=ghost", () => {
    const wrapper = mount(BaseButton, {
      props: { variant: "ghost" }, slots: { default: "Cancel" },
    });
    expect(wrapper.classes()).toContain("bg-transparent");
  });
});
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd frontend && npm run test`
Expected: PASS (3 passed)

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/
git commit -m "feat(frontend): shared UI components (button, input, skeleton, stagger)"
```

---

## Task 19: API client, auth store, router with guard

**Files:**
- Create: `frontend/src/core/api.ts`
- Create: `frontend/src/core/stores/auth.ts`
- Create: `frontend/src/core/router.ts`
- Test: `frontend/src/core/stores/auth.test.ts`

- [ ] **Step 1: Create `frontend/src/core/api.ts`**

```ts
const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface ApiOptions {
  method?: string;
  body?: unknown;
  token?: string | null;
}

export async function api<T>(path: string, opts: ApiOptions = {}): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (opts.token) headers["Authorization"] = `Bearer ${opts.token}`;
  const res = await fetch(`${BASE}${path}`, {
    method: opts.method ?? "GET",
    headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}
```

- [ ] **Step 2: Create `frontend/src/core/stores/auth.ts`**

```ts
import { defineStore } from "pinia";
import { api } from "@/core/api";

interface TokenPair { access_token: string; refresh_token: string }
interface User { id: string; tenant_id: string; email: string; name: string; role: string }

const ACCESS = "access_token";
const REFRESH = "refresh_token";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    accessToken: localStorage.getItem(ACCESS) as string | null,
    refreshToken: localStorage.getItem(REFRESH) as string | null,
    user: null as User | null,
  }),
  getters: {
    isAuthenticated: (s) => !!s.accessToken,
  },
  actions: {
    setTokens(t: TokenPair) {
      this.accessToken = t.access_token;
      this.refreshToken = t.refresh_token;
      localStorage.setItem(ACCESS, t.access_token);
      localStorage.setItem(REFRESH, t.refresh_token);
    },
    async signup(payload: { company_name: string; name: string; email: string; password: string }) {
      this.setTokens(await api<TokenPair>("/auth/signup", { method: "POST", body: payload }));
      await this.fetchMe();
    },
    async login(email: string, password: string) {
      this.setTokens(await api<TokenPair>("/auth/login", { method: "POST", body: { email, password } }));
      await this.fetchMe();
    },
    async fetchMe() {
      this.user = await api<User>("/auth/me", { token: this.accessToken });
    },
    logout() {
      this.accessToken = null;
      this.refreshToken = null;
      this.user = null;
      localStorage.removeItem(ACCESS);
      localStorage.removeItem(REFRESH);
    },
  },
});
```

- [ ] **Step 3: Create `frontend/src/core/router.ts`**

```ts
import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { useAuthStore } from "@/core/stores/auth";

const routes: RouteRecordRaw[] = [
  { path: "/login", name: "login", component: () => import("@/pages/LoginPage.vue") },
  { path: "/signup", name: "signup", component: () => import("@/pages/SignupPage.vue") },
  {
    path: "/",
    component: () => import("@/layouts/AppShell.vue"),
    meta: { requiresAuth: true },
    children: [
      { path: "", name: "dashboard", component: () => import("@/pages/DashboardPage.vue") },
    ],
  },
];

export const router = createRouter({ history: createWebHistory(), routes });

router.beforeEach((to) => {
  const auth = useAuthStore();
  if (to.meta.requiresAuth && !auth.isAuthenticated) return { name: "login" };
  if ((to.name === "login" || to.name === "signup") && auth.isAuthenticated) {
    return { name: "dashboard" };
  }
  return true;
});
```

- [ ] **Step 4: Write the test `frontend/src/core/stores/auth.test.ts`**

```ts
import { setActivePinia, createPinia } from "pinia";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { useAuthStore } from "./auth";

describe("auth store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
  });

  it("starts unauthenticated", () => {
    const auth = useAuthStore();
    expect(auth.isAuthenticated).toBe(false);
  });

  it("setTokens marks authenticated and persists", () => {
    const auth = useAuthStore();
    auth.setTokens({ access_token: "a", refresh_token: "r" });
    expect(auth.isAuthenticated).toBe(true);
    expect(localStorage.getItem("access_token")).toBe("a");
  });

  it("logout clears state and storage", () => {
    const auth = useAuthStore();
    auth.setTokens({ access_token: "a", refresh_token: "r" });
    auth.logout();
    expect(auth.isAuthenticated).toBe(false);
    expect(localStorage.getItem("access_token")).toBeNull();
  });
});
```

- [ ] **Step 5: Run the test, then build**

Run: `cd frontend && npm run test`
Expected: auth store tests PASS (3 passed). (Note: pages/layouts referenced by the router are created in Task 20–21; the build check happens at Task 21 Step 6.)

- [ ] **Step 6: Commit**

```bash
git add frontend/src/core/
git commit -m "feat(frontend): API client, auth store, router with guard"
```

---

## Task 20: App shell layout

**Files:**
- Create: `frontend/src/layouts/AppShell.vue`
- Create: `frontend/src/pages/DashboardPage.vue`

- [ ] **Step 1: Create `frontend/src/layouts/AppShell.vue`**

```vue
<script setup lang="ts">
import { RouterView, useRouter } from "vue-router";
import { useAuthStore } from "@/core/stores/auth";
import { onMounted } from "vue";

const auth = useAuthStore();
const router = useRouter();

onMounted(() => {
  if (auth.isAuthenticated && !auth.user) auth.fetchMe().catch(() => auth.logout());
});

function logout() {
  auth.logout();
  router.push({ name: "login" });
}
</script>

<template>
  <div class="flex min-h-[100dvh]">
    <!-- Sidebar -->
    <aside class="w-60 shrink-0 border-r border-border bg-surface/60 backdrop-blur-md p-4 flex flex-col">
      <div class="font-display text-lg font-bold mb-8">
        <span class="text-accent">◆</span> Pipeline
      </div>
      <nav class="flex flex-col gap-1 text-sm">
        <RouterLink to="/" class="rounded-lg px-3 py-2 hover:bg-surface-raised" active-class="bg-surface-raised text-accent">
          Dashboard
        </RouterLink>
        <div class="mt-4 mb-1 text-xs uppercase tracking-wider text-muted px-3">CRM</div>
        <span class="rounded-lg px-3 py-2 text-muted cursor-not-allowed">Pipeline (Phase 1)</span>
        <div class="mt-4 mb-1 text-xs uppercase tracking-wider text-muted px-3">HR</div>
        <span class="rounded-lg px-3 py-2 text-muted cursor-not-allowed">Employees (Phase 2)</span>
      </nav>
      <div class="mt-auto">
        <div class="text-sm text-ink">{{ auth.user?.name }}</div>
        <div class="text-xs text-muted mb-2">{{ auth.user?.email }}</div>
        <button class="text-xs text-muted hover:text-ink" @click="logout">Sign out</button>
      </div>
    </aside>

    <!-- Main -->
    <main class="flex-1 p-6 overflow-auto">
      <RouterView />
    </main>
  </div>
</template>
```

- [ ] **Step 2: Create `frontend/src/pages/DashboardPage.vue`**

```vue
<script setup lang="ts">
import { useAuthStore } from "@/core/stores/auth";
const auth = useAuthStore();
</script>

<template>
  <div>
    <h1 class="font-display text-2xl font-bold mb-1">
      Welcome{{ auth.user ? `, ${auth.user.name}` : "" }}
    </h1>
    <p class="text-muted mb-8">Your workspace is ready. CRM and HR modules land next.</p>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div
        v-for="(card, i) in [
          { label: 'Sales Pipeline', body: 'Kanban board for leads & deals', tag: 'Phase 1' },
          { label: 'Team & HR', body: 'Directory, attendance, leave', tag: 'Phase 2' },
          { label: 'Custom Views', body: 'Saved filters & shared views', tag: 'Phase 1' },
        ]"
        :key="i"
        class="stagger-item rounded-xl2 border border-border bg-surface-raised/70 backdrop-blur-md p-5"
        :style="{ animationDelay: `${i * 80}ms` }"
      >
        <div class="text-xs uppercase tracking-wider text-accent mb-2">{{ card.tag }}</div>
        <div class="font-display font-semibold mb-1">{{ card.label }}</div>
        <div class="text-sm text-muted">{{ card.body }}</div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/layouts/AppShell.vue frontend/src/pages/DashboardPage.vue
git commit -m "feat(frontend): app shell layout + dashboard landing"
```

---

## Task 21: Login and signup pages

**Files:**
- Create: `frontend/src/pages/LoginPage.vue`
- Create: `frontend/src/pages/SignupPage.vue`
- Create: `frontend/.env.example`

- [ ] **Step 1: Create `frontend/src/pages/LoginPage.vue`**

```vue
<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/core/stores/auth";
import BaseButton from "@/components/BaseButton.vue";
import BaseInput from "@/components/BaseInput.vue";

const email = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);
const auth = useAuthStore();
const router = useRouter();

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function submit() {
  error.value = "";
  loading.value = true;
  try {
    await auth.login(email.value, password.value);
    router.push({ name: "dashboard" });
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="min-h-[100dvh] flex items-center justify-center p-4">
    <div class="w-full max-w-sm rounded-xl2 border border-border bg-surface-raised/70 backdrop-blur-md p-8 stagger-item">
      <div class="font-display text-2xl font-bold mb-1"><span class="text-accent">◆</span> Welcome back</div>
      <p class="text-muted text-sm mb-6">Sign in to your workspace</p>

      <form class="flex flex-col gap-3" @submit.prevent="submit">
        <BaseInput v-model="email" type="email" placeholder="Email" />
        <BaseInput v-model="password" type="password" placeholder="Password" />
        <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
        <BaseButton type="submit">{{ loading ? "Signing in…" : "Sign in" }}</BaseButton>
      </form>

      <a :href="`${API}/auth/google/login`"
         class="mt-3 flex items-center justify-center gap-2 rounded-xl border border-border py-2 text-sm hover:bg-surface">
        Continue with Google
      </a>

      <p class="text-sm text-muted mt-6 text-center">
        No account?
        <RouterLink to="/signup" class="text-accent">Create one</RouterLink>
      </p>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Create `frontend/src/pages/SignupPage.vue`**

```vue
<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/core/stores/auth";
import BaseButton from "@/components/BaseButton.vue";
import BaseInput from "@/components/BaseInput.vue";

const companyName = ref("");
const name = ref("");
const email = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);
const auth = useAuthStore();
const router = useRouter();

async function submit() {
  error.value = "";
  loading.value = true;
  try {
    await auth.signup({
      company_name: companyName.value, name: name.value,
      email: email.value, password: password.value,
    });
    router.push({ name: "dashboard" });
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="min-h-[100dvh] flex items-center justify-center p-4">
    <div class="w-full max-w-sm rounded-xl2 border border-border bg-surface-raised/70 backdrop-blur-md p-8 stagger-item">
      <div class="font-display text-2xl font-bold mb-1"><span class="text-accent">◆</span> Create workspace</div>
      <p class="text-muted text-sm mb-6">Start your free CRM + HR workspace</p>

      <form class="flex flex-col gap-3" @submit.prevent="submit">
        <BaseInput v-model="companyName" placeholder="Company name" />
        <BaseInput v-model="name" placeholder="Your name" />
        <BaseInput v-model="email" type="email" placeholder="Email" />
        <BaseInput v-model="password" type="password" placeholder="Password (min 8 chars)" />
        <p v-if="error" class="text-sm text-red-400">{{ error }}</p>
        <BaseButton type="submit">{{ loading ? "Creating…" : "Create workspace" }}</BaseButton>
      </form>

      <p class="text-sm text-muted mt-6 text-center">
        Already have an account?
        <RouterLink to="/login" class="text-accent">Sign in</RouterLink>
      </p>
    </div>
  </div>
</template>
```

- [ ] **Step 3: Create `frontend/.env.example`**

```
VITE_API_URL=http://localhost:8000
```

- [ ] **Step 4: Run frontend tests**

Run: `cd frontend && npm run test`
Expected: PASS (BaseButton + auth store = 6 passed total).

- [ ] **Step 5: Build the frontend**

Run: `cd frontend && npm run build`
Expected: `vue-tsc` type-check passes and Vite produces `dist/`. Fix any type errors before committing.

- [ ] **Step 6: Manual smoke test (optional but recommended)**

Run backend (`cd backend && uvicorn app.main:app --reload`) and frontend (`cd frontend && npm run dev`). Visit `http://localhost:5173/signup`, create a workspace, confirm redirect to the dashboard with staggered card reveal and the sidebar showing your name.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/ frontend/.env.example
git commit -m "feat(frontend): login and signup pages with Google option"
```

---

## Task 22: Deployment configuration

**Files:**
- Create: `backend/render.yaml`
- Create: `frontend/vercel.json`
- Create: `backend/Dockerfile` (optional, for Render Docker deploy)
- Create: `README.md`

- [ ] **Step 1: Create `backend/render.yaml`**

```yaml
services:
  - type: web
    name: crm-hr-backend
    runtime: python
    buildCommand: "pip install -e . && alembic upgrade head"
    startCommand: "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: JWT_SECRET
        generateValue: true
      - key: GOOGLE_CLIENT_ID
        sync: false
      - key: GOOGLE_CLIENT_SECRET
        sync: false
      - key: GOOGLE_REDIRECT_URI
        sync: false
      - key: FRONTEND_URL
        sync: false
```

- [ ] **Step 2: Create `frontend/vercel.json`**

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

- [ ] **Step 3: Create `README.md`**

```markdown
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
```

- [ ] **Step 4: Commit**

```bash
git add backend/render.yaml frontend/vercel.json README.md
git commit -m "chore: deployment configs for Render + Vercel and project README"
```

---

## Self-Review Notes (resolved during planning)

- **Spec coverage:** Phase 0 covers spec §3 (architecture/stacks), §4 core tables (tenants, users — CRM/HR tables deferred to their phases), §7 design system (tokens, fonts, stagger, skeleton, reduced-motion, 16px inputs), §8 auth (email/password + Google + invites + roles), §9 multi-tenancy (RLS + tenant context), and §11 build order. CRM/HR feature tables (§5, §6) and real-time (§10) are intentionally deferred to Phase 1/2 plans.
- **Login vs RLS:** resolved with the `login_lookup` permissive SELECT policy (Task 11 Step 3) so authentication can find users before a tenant context exists, while `tenant_isolation` governs all in-request access.
- **RLS testing:** requires a non-superuser DB role; documented in Task 7 Step 3 and Task 8 Step 5.
- **Type consistency:** `set_tenant`, `get_tenant_session`, `create_access_token`/`create_refresh_token`/`decode_token`, `TokenPair`, `UserOut`, and the auth-store method names (`setTokens`, `fetchMe`, `login`, `signup`, `logout`) are used identically across all tasks.

---

## Open Items Deferred to Phase 1/2 Plans
- CRM and HR data-model tables + their RLS policies (same pattern as Task 7).
- Real-time WebSocket layer (spec §10).
- Full role/permission matrix beyond admin/member.
- Production email provider (Resend) swapped in for `ConsoleEmailSender`.
- "Convert to Deal" link-vs-copy semantics.
