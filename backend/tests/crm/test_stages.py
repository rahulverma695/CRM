import pytest


async def test_create_stage(client, tenant_and_admin):
    _, _, headers = tenant_and_admin
    resp = await client.post(
        "/crm/stages",
        json={"name": "Qualified", "color": "#ff0", "order": 1, "type": "lead"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Qualified"
    assert data["type"] == "lead"


async def test_list_stages_returns_own_tenant_only(client, tenant_and_admin, stage):
    _, _, headers = tenant_and_admin
    resp = await client.get("/crm/stages", headers=headers)
    assert resp.status_code == 200
    ids = [s["id"] for s in resp.json()]
    assert str(stage.id) in ids


async def test_update_stage(client, tenant_and_admin, stage):
    _, _, headers = tenant_and_admin
    resp = await client.patch(
        f"/crm/stages/{stage.id}",
        json={"name": "Renamed"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"


async def test_delete_stage(client, tenant_and_admin, stage):
    _, _, headers = tenant_and_admin
    resp = await client.delete(f"/crm/stages/{stage.id}", headers=headers)
    assert resp.status_code == 204
