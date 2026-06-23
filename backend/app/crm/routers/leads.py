import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_tenant_session, get_current_claims
from app.crm.models import Lead, Activity
from app.crm.schemas import LeadIn, LeadPatch, LeadOut

try:
    from app.core.ws import manager as ws_manager
except ImportError:
    ws_manager = None

router = APIRouter(prefix="/crm/leads", tags=["crm-leads"])


@router.get("", response_model=list[LeadOut])
async def list_leads(
    stage_id: uuid.UUID | None = Query(None),
    owner_id: uuid.UUID | None = Query(None),
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    q = select(Lead).order_by(Lead.created_at.desc())
    if stage_id:
        q = q.where(Lead.stage_id == stage_id)
    if owner_id:
        q = q.where(Lead.owner_id == owner_id)
    rows = await session.execute(q)
    return rows.scalars().all()


@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead(
    lead_id: uuid.UUID,
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    lead = await session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404)
    return lead


@router.post("", response_model=LeadOut, status_code=201)
async def create_lead(
    body: LeadIn,
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    lead = Lead(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(claims["tenant_id"]),
        **body.model_dump(),
    )
    session.add(lead)
    await session.commit()
    await session.refresh(lead)
    return lead


@router.patch("/{lead_id}", response_model=LeadOut)
async def update_lead(
    lead_id: uuid.UUID,
    body: LeadPatch,
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    lead = await session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404)

    updates = body.model_dump(exclude_none=True)
    old_stage = lead.stage_id

    for field, value in updates.items():
        setattr(lead, field, value)

    # record stage change activity
    if "stage_id" in updates and updates["stage_id"] != old_stage:
        activity = Activity(
            id=uuid.uuid4(),
            tenant_id=lead.tenant_id,
            lead_id=lead.id,
            type="stage_change",
            content={"from": str(old_stage), "to": str(updates["stage_id"])},
            created_by=uuid.UUID(claims["sub"]),
        )
        session.add(activity)

    await session.commit()
    await session.refresh(lead)

    # broadcast Kanban move
    if "stage_id" in updates and ws_manager is not None:
        await ws_manager.broadcast(
            f"kanban:{claims['tenant_id']}",
            {"event": "lead_moved", "lead_id": str(lead_id),
             "stage_id": str(lead.stage_id)},
        )

    return lead


@router.delete("/{lead_id}", status_code=204)
async def delete_lead(
    lead_id: uuid.UUID,
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    lead = await session.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404)
    await session.delete(lead)
    await session.commit()
