import uuid
import pytest
from app.core.security.jwt import create_access_token
from app.core.security.passwords import hash_password
from app.core.models.tenant import Tenant
from app.core.models.user import User
from app.core.middleware.tenant_context import set_tenant


@pytest.fixture
async def tenant_and_admin(session):
    """Creates one tenant + admin user, returns (tenant, user, auth_headers)."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Test Co",
        slug=f"testco-{uuid.uuid4().hex[:6]}",
        plan="free",
    )
    session.add(tenant)
    await session.flush()

    await set_tenant(session, str(tenant.id))

    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email=f"admin-{uuid.uuid4().hex[:4]}@test.com",
        name="Admin",
        role="admin",
        password_hash=hash_password("pw"),
        is_active=True,
    )
    session.add(user)
    await session.commit()

    token = create_access_token(str(user.id), str(tenant.id), "admin")
    headers = {"Authorization": f"Bearer {token}"}
    return tenant, user, headers


@pytest.fixture
async def stage(tenant_and_admin, session):
    from app.crm.models import PipelineStage
    tenant, user, _ = tenant_and_admin
    await set_tenant(session, str(tenant.id))
    s = PipelineStage(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name="New",
        color="#c6f24e",
        order=0,
        type="lead",
    )
    session.add(s)
    await session.commit()
    return s


@pytest.fixture
async def lead(tenant_and_admin, stage, session):
    from app.crm.models import Lead
    tenant, user, _ = tenant_and_admin
    await set_tenant(session, str(tenant.id))
    l = Lead(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        stage_id=stage.id,
        owner_id=user.id,
    )
    session.add(l)
    await session.commit()
    return l
