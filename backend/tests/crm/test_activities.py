import uuid
import pytest
from app.core.middleware.tenant_context import set_tenant


async def test_create_note_activity(client, tenant_and_admin, lead):
    _, _, headers = tenant_and_admin
    resp = await client.post(
        "/crm/activities",
        json={"lead_id": str(lead.id), "type": "note",
              "content": {"text": "Called and discussed pricing"}},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["type"] == "note"


async def test_list_activities_requires_lead_or_deal(client, tenant_and_admin):
    _, _, headers = tenant_and_admin
    resp = await client.get("/crm/activities", headers=headers)
    assert resp.status_code == 400


async def test_list_activities_by_lead(client, tenant_and_admin, lead, session):
    from app.crm.models import Activity
    tenant, user, headers = tenant_and_admin
    await set_tenant(session, str(tenant.id))
    a = Activity(
        id=uuid.uuid4(), tenant_id=tenant.id, lead_id=lead.id,
        type="note", content={"text": "hi"}, created_by=user.id
    )
    session.add(a)
    await session.commit()
    resp = await client.get(f"/crm/activities?lead_id={lead.id}", headers=headers)
    assert resp.status_code == 200
    assert any(x["id"] == str(a.id) for x in resp.json())
