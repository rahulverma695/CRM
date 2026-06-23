import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_tenant_session, get_current_claims
from app.crm.models import PipelineStage
from app.crm.schemas import StageIn, StagePatch, StageOut

router = APIRouter(prefix="/crm/stages", tags=["crm-stages"])


@router.get("", response_model=list[StageOut])
async def list_stages(
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    rows = await session.execute(
        select(PipelineStage).order_by(PipelineStage.order)
    )
    return rows.scalars().all()


@router.post("", response_model=StageOut, status_code=201)
async def create_stage(
    body: StageIn,
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    stage = PipelineStage(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(claims["tenant_id"]),
        **body.model_dump(),
    )
    session.add(stage)
    await session.commit()
    await session.refresh(stage)
    return stage


@router.patch("/{stage_id}", response_model=StageOut)
async def update_stage(
    stage_id: uuid.UUID,
    body: StagePatch,
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    stage = await session.get(PipelineStage, stage_id)
    if not stage:
        raise HTTPException(404)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(stage, field, value)
    await session.commit()
    await session.refresh(stage)
    return stage


@router.delete("/{stage_id}", status_code=204)
async def delete_stage(
    stage_id: uuid.UUID,
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    stage = await session.get(PipelineStage, stage_id)
    if not stage:
        raise HTTPException(404)
    await session.delete(stage)
    await session.commit()
