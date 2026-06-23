import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_tenant_session, get_current_claims
from app.crm.models import Deal
from app.crm.schemas import DealIn, DealPatch, DealOut

router = APIRouter(prefix="/crm/deals", tags=["crm-deals"])


@router.get("", response_model=list[DealOut])
async def list_deals(
    lead_id: uuid.UUID | None = Query(None),
    stage_id: uuid.UUID | None = Query(None),
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    q = select(Deal).order_by(Deal.created_at.desc())
    if lead_id:
        q = q.where(Deal.lead_id == lead_id)
    if stage_id:
        q = q.where(Deal.stage_id == stage_id)
    rows = await session.execute(q)
    return rows.scalars().all()


@router.get("/{deal_id}", response_model=DealOut)
async def get_deal(
    deal_id: uuid.UUID,
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    deal = await session.get(Deal, deal_id)
    if not deal:
        raise HTTPException(404)
    return deal


@router.post("", response_model=DealOut, status_code=201)
async def create_deal(
    body: DealIn,
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    deal = Deal(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(claims["tenant_id"]),
        **body.model_dump(),
    )
    session.add(deal)
    await session.commit()
    await session.refresh(deal)
    return deal


@router.patch("/{deal_id}", response_model=DealOut)
async def update_deal(
    deal_id: uuid.UUID,
    body: DealPatch,
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    deal = await session.get(Deal, deal_id)
    if not deal:
        raise HTTPException(404)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(deal, field, value)
    await session.commit()
    await session.refresh(deal)
    return deal


@router.delete("/{deal_id}", status_code=204)
async def delete_deal(
    deal_id: uuid.UUID,
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    deal = await session.get(Deal, deal_id)
    if not deal:
        raise HTTPException(404)
    await session.delete(deal)
    await session.commit()
