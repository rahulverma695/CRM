import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_tenant_session, get_current_claims
from app.crm.models import CrmTask
from app.crm.schemas import CrmTaskIn, CrmTaskPatch, CrmTaskOut

router = APIRouter(prefix="/crm/tasks", tags=["crm-tasks"])


@router.get("", response_model=list[CrmTaskOut])
async def list_tasks(
    lead_id: uuid.UUID | None = Query(None),
    deal_id: uuid.UUID | None = Query(None),
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    q = select(CrmTask).order_by(CrmTask.due_date.asc().nulls_last())
    if lead_id:
        q = q.where(CrmTask.lead_id == lead_id)
    if deal_id:
        q = q.where(CrmTask.deal_id == deal_id)
    rows = await session.execute(q)
    return rows.scalars().all()


@router.post("", response_model=CrmTaskOut, status_code=201)
async def create_task(
    body: CrmTaskIn,
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    task = CrmTask(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(claims["tenant_id"]),
        **body.model_dump(),
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


@router.patch("/{task_id}", response_model=CrmTaskOut)
async def update_task(
    task_id: uuid.UUID,
    body: CrmTaskPatch,
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    task = await session.get(CrmTask, task_id)
    if not task:
        raise HTTPException(404)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(task, field, value)
    await session.commit()
    await session.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: uuid.UUID,
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    task = await session.get(CrmTask, task_id)
    if not task:
        raise HTTPException(404)
    await session.delete(task)
    await session.commit()
