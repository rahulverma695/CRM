import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings
from app.main import create_app
from app.database import get_session
from app.core.routers.oauth import resolve_google_email

TEST_URL = settings.test_database_url or settings.database_url


def _build_app(fake_email: str):
    app = create_app()
    test_engine = create_async_engine(TEST_URL)
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_get_session():
        async with factory() as s:
            yield s

    async def _fake_resolver():
        return fake_email

    app.dependency_overrides[get_session] = _override_get_session
    app.dependency_overrides[resolve_google_email] = _fake_resolver
    return app, test_engine


async def test_google_callback_existing_user():
    app, engine = _build_app("oauthuser@globex.com")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test",
                           follow_redirects=False) as c:
        # create the user first via signup (same app/DB)
        await c.post("/auth/signup", json={
            "company_name": "Globex OAuth", "name": "OAuth Sara",
            "email": "oauthuser@globex.com", "password": "supersecret",
        })
        resp = await c.get("/auth/google/callback")
    await engine.dispose()
    assert resp.status_code in (302, 307)
    assert "access=" in resp.headers["location"]


async def test_google_callback_unknown_user():
    app, engine = _build_app("ghost-oauth@nowhere.com")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test",
                           follow_redirects=False) as c:
        resp = await c.get("/auth/google/callback")
    await engine.dispose()
    assert resp.status_code == 404
