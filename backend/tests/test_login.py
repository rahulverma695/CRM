import pytest


@pytest.fixture
async def signed_up(client):
    await client.post("/auth/signup", json={
        "company_name": "Initech", "name": "Bill", "email": "bill@initech.com",
        "password": "supersecret",
    })


@pytest.mark.asyncio
async def test_login_success(client, signed_up):
    resp = await client.post("/auth/login", json={
        "email": "bill@initech.com", "password": "supersecret",
    })
    assert resp.status_code == 200
    assert resp.json()["access_token"]


@pytest.mark.asyncio
async def test_login_wrong_password(client, signed_up):
    resp = await client.post("/auth/login", json={
        "email": "bill@initech.com", "password": "wrongpass",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    resp = await client.post("/auth/login", json={
        "email": "nobody@nowhere.com", "password": "supersecret",
    })
    assert resp.status_code == 401
