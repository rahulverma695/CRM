import pytest


@pytest.mark.asyncio
async def test_refresh_issues_new_access_token(client):
    signup = await client.post("/auth/signup", json={
        "company_name": "Umbrella", "name": "Alice", "email": "alice@umbrella.com",
        "password": "supersecret",
    })
    refresh_token = signup.json()["refresh_token"]
    resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


@pytest.mark.asyncio
async def test_refresh_rejects_access_token(client):
    signup = await client.post("/auth/signup", json={
        "company_name": "Stark", "name": "Tony", "email": "tony@stark.com",
        "password": "supersecret",
    })
    access_token = signup.json()["access_token"]
    resp = await client.post("/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401
