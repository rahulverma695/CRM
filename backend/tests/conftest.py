import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.config import settings
from app.core.models import Tenant, User
from app.core.security.passwords import hash_password

TEST_URL = settings.test_database_url or settings.database_url


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    engine = create_async_engine(TEST_URL)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
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
