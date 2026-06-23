import uuid
import pytest
from app.core.middleware.tenant_context import set_tenant


@pytest.fixture
async def deal(tenant_and_admin, lead, session):
    from app.crm.models import Deal
    tenant, user, _ = tenant_and_admin
    await set_tenant(session, str(tenant.id))
    d = Deal(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        title="Big Deal",
        lead_id=lead.id,
        value=50000.0,
        currency="USD",
    )
    session.add(d)
    await session.commit()
    return d


async def test_create_deal(client, tenant_and_admin, lead):
    _, _, headers = tenant_and_admin
    resp = await client.post(
        "/crm/deals",
        json={"title": "Enterprise Deal", "lead_id": str(lead.id),
              "value": 10000.0, "currency": "USD"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["title"] == "Enterprise Deal"


async def test_list_deals_by_lead(client, tenant_and_admin, deal, lead):
    _, _, headers = tenant_and_admin
    resp = await client.get(f"/crm/deals?lead_id={lead.id}", headers=headers)
    assert resp.status_code == 200
    assert any(d["id"] == str(deal.id) for d in resp.json())


async def test_update_deal(client, tenant_and_admin, deal):
    _, _, headers = tenant_and_admin
    resp = await client.patch(
        f"/crm/deals/{deal.id}",
        json={"value": 75000.0, "probability": 80},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["value"] == 75000.0
