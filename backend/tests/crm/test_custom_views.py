import uuid
import pytest
from app.core.middleware.tenant_context import set_tenant
from app.core.security.jwt import create_access_token
from app.core.security.passwords import hash_password


async def test_create_and_list_view(client, tenant_and_admin):
    _, _, headers = tenant_and_admin
    resp = await client.post(
        "/crm/views",
        json={"name": "Hot Leads", "filters": {"source": "website"},
              "is_shared": False},
        headers=headers,
    )
    assert resp.status_code == 201
    view_id = resp.json()["id"]

    resp2 = await client.get("/crm/views", headers=headers)
    assert any(v["id"] == view_id for v in resp2.json())


async def test_non_owner_cannot_edit_view(client, tenant_and_admin, session):
    from app.crm.models import CustomView
    from app.core.models.user import User

    tenant, owner, owner_headers = tenant_and_admin
    await set_tenant(session, str(tenant.id))

    other_user = User(
        id=uuid.uuid4(), tenant_id=tenant.id,
        email=f"other-{uuid.uuid4().hex[:4]}@test.com",
        name="Other", role="member",
        password_hash=hash_password("pw"), is_active=True,
    )
    session.add(other_user)
    view = CustomView(
        id=uuid.uuid4(), tenant_id=tenant.id, user_id=owner.id,
        name="Private", filters={}, columns=[], is_shared=False,
    )
    session.add(view)
    await session.commit()

    other_token = create_access_token(
        {"sub": str(other_user.id), "tenant_id": str(tenant.id), "role": "member"}
    )
    resp = await client.patch(
        f"/crm/views/{view.id}",
        json={"name": "Hacked"},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert resp.status_code == 403
