from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def set_tenant(session: AsyncSession, tenant_id: str) -> None:
    """Set the per-transaction tenant id used by RLS policies.

    Uses set_config(..., is_local => true) so the setting is scoped to the
    current transaction and does not leak across pooled connections.

    FAIL-CLOSED: every query against a tenant-scoped table MUST be preceded by
    a call to this function within the same transaction. If app.tenant_id is
    unset, current_setting('app.tenant_id', true) returns NULL, the RLS policy
    `tenant_id = NULL` is never true, and the query returns ZERO rows (it does
    not error). Request handlers obtain a tenant-scoped session via
    get_tenant_session (see app/core/deps.py), which calls this for them.
    """
    await session.execute(
        text("SELECT set_config('app.tenant_id', :tid, true)"),
        {"tid": str(tenant_id)},
    )
