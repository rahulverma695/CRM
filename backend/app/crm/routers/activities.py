import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_tenant_session, get_current_claims
from app.crm.models import Activity
from app.crm.schemas import ActivityIn, ActivityOut

try:
    from app.core.ws import manager as ws_manager
except ImportError:
    ws_manager = None

router = APIRouter(prefix="/crm/activities", tags=["crm-activities"])


@router.get("", response_model=list[ActivityOut])
async def list_activities(
    lead_id: uuid.UUID | None = Query(None),
    deal_id: uuid.UUID | None = Query(None),
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    if not lead_id and not deal_id:
        raise HTTPException(400, "Provide lead_id or deal_id")
    q = select(Activity).order_by(Activity.created_at.asc())
    if lead_id:
        q = q.where(Activity.lead_id == lead_id)
    if deal_id:
        q = q.where(Activity.deal_id == deal_id)
    rows = await session.execute(q)
    return rows.scalars().all()


@router.post("", response_model=ActivityOut, status_code=201)
async def create_activity(
    body: ActivityIn,
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    activity = Activity(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(claims["tenant_id"]),
        created_by=uuid.UUID(claims["sub"]),
        **body.model_dump(),
    )
    session.add(activity)
    await session.commit()
    await session.refresh(activity)

    if ws_manager is not None:
        await ws_manager.broadcast(
            f"kanban:{claims['tenant_id']}",
            {"event": "activity_added",
             "lead_id": str(body.lead_id) if body.lead_id else None,
             "deal_id": str(body.deal_id) if body.deal_id else None,
             "type": body.type},
        )

    return activity
