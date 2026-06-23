import pytest_asyncio
from app.core.email import email_sender


@pytest_asyncio.fixture
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


async def test_duplicate_invite_returns_409(client, admin_token):
    email_sender.sent.clear()
    first = await client.post("/invites", json={
        "email": "dup@wonka.com", "name": "Dup", "role": "member",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert first.status_code == 201
    second = await client.post("/invites", json={
        "email": "dup@wonka.com", "name": "Dup Again", "role": "member",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert second.status_code == 409


async def test_accept_invite_twice_is_rejected(client, admin_token):
    email_sender.sent.clear()
    await client.post("/invites", json={
        "email": "twice@wonka.com", "name": "Twice", "role": "member",
    }, headers={"Authorization": f"Bearer {admin_token}"})
    token = email_sender.sent[0]["body"].split("token=")[1].strip()
    first = await client.post("/invites/accept", json={"token": token, "password": "secret123"})
    assert first.status_code == 200
    second = await client.post("/invites/accept", json={"token": token, "password": "newsecret123"})
    assert second.status_code == 409
