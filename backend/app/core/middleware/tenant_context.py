from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def set_tenant(session: AsyncSession, tenant_id: str) -> None:
    """Set the per-transaction tenant id used by RLS policies.

    Uses set_config(..., is_local => true) so the setting is scoped to the
    current transaction and does not leak across pooled connections.
    """
    await session.execute(
        text("SELECT set_config('app.tenant_id', :tid, true)"),
        {"tid": str(tenant_id)},
    )
