import uuid
from sqlalchemy import select, text
from app.core.models import User
from app.core.middleware.tenant_context import set_tenant


async def test_rls_scopes_to_current_tenant(session, two_tenants):
    a_id, b_id = two_tenants

    await set_tenant(session, str(a_id))
    rows = (await session.execute(select(User))).scalars().all()
    assert len(rows) == 1
    assert rows[0].tenant_id == a_id


async def test_rls_blocks_cross_tenant_read(session, two_tenants):
    a_id, b_id = two_tenants

    await set_tenant(session, str(b_id))
    rows = (await session.execute(select(User))).scalars().all()
    assert all(r.tenant_id == b_id for r in rows)
    assert a_id not in {r.tenant_id for r in rows}
