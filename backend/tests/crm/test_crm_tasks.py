import uuid
import pytest
from app.core.middleware.tenant_context import set_tenant


async def test_create_task(client, tenant_and_admin, lead):
    _, _, headers = tenant_and_admin
    resp = await client.post(
        "/crm/tasks",
        json={"title": "Follow up call", "lead_id": str(lead.id)},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "open"


async def test_complete_task(client, tenant_and_admin, lead, session):
    from app.crm.models import CrmTask
    tenant, user, headers = tenant_and_admin
    await set_tenant(session, str(tenant.id))
    t = CrmTask(id=uuid.uuid4(), tenant_id=tenant.id,
                title="Do thing", lead_id=lead.id, status="open")
    session.add(t)
    await session.commit()

    resp = await client.patch(f"/crm/tasks/{t.id}", json={"status": "done"},
                              headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"
