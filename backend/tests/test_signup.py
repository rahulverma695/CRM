import pytest


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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
