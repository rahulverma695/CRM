import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from httpx import AsyncClient, ASGITransport
from app.config import settings
from app.core.models import Tenant, User
from app.core.security.passwords import hash_password

TEST_URL = settings.test_database_url or settings.database_url


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    """Async session for tests.

    SECURITY: must connect as a role WITHOUT the BYPASSRLS attribute, or RLS
    policies are silently skipped and these isolation tests give false positives.
    The assertion below fails loudly if TEST_DATABASE_URL points at a
    BYPASSRLS/owner role.
    """
    engine = create_async_engine(TEST_URL)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        bypass = await s.scalar(
            text("SELECT rolbypassrls FROM pg_roles WHERE rolname = current_user")
        )
        assert bypass is False, (
            "Test DB role bypasses RLS — isolation tests would be meaningless. "
            "Point TEST_DATABASE_URL at the NOBYPASSRLS app_user role."
        )
        yield s
    await engine.dispose()


@pytest_asyncio.fixture
async def two_tenants(session):
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


@pytest_asyncio.fixture
async def client():
    from app.main import create_app
    from app.database import get_session

    app = create_app()
    test_engine = create_async_engine(TEST_URL)
    test_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_get_session():
        async with test_factory() as s:
            yield s

    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await test_engine.dispose()
