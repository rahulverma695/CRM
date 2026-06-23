import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_tenant_session, get_current_claims
from app.crm.models import CustomView
from app.crm.schemas import CustomViewIn, CustomViewPatch, CustomViewOut

router = APIRouter(prefix="/crm/views", tags=["crm-views"])


@router.get("", response_model=list[CustomViewOut])
async def list_views(
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    user_id = uuid.UUID(claims["sub"])
    rows = await session.execute(
        select(CustomView).where(
            or_(CustomView.user_id == user_id, CustomView.is_shared.is_(True))
        ).order_by(CustomView.created_at.desc())
    )
    return rows.scalars().all()


@router.post("", response_model=CustomViewOut, status_code=201)
async def create_view(
    body: CustomViewIn,
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    view = CustomView(
        id=uuid.uuid4(),
        tenant_id=uuid.UUID(claims["tenant_id"]),
        user_id=uuid.UUID(claims["sub"]),
        **body.model_dump(),
    )
    session.add(view)
    await session.commit()
    await session.refresh(view)
    return view


@router.patch("/{view_id}", response_model=CustomViewOut)
async def update_view(
    view_id: uuid.UUID,
    body: CustomViewPatch,
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    view = await session.get(CustomView, view_id)
    if not view:
        raise HTTPException(404)
    if str(view.user_id) != claims["sub"]:
        raise HTTPException(403, "Only the view owner can edit it")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(view, field, value)
    await session.commit()
    await session.refresh(view)
    return view


@router.delete("/{view_id}", status_code=204)
async def delete_view(
    view_id: uuid.UUID,
    claims: dict = Depends(get_current_claims),
    session: AsyncSession = Depends(get_tenant_session),
):
    view = await session.get(CustomView, view_id)
    if not view:
        raise HTTPException(404)
    if str(view.user_id) != claims["sub"]:
        raise HTTPException(403)
    await session.delete(view)
    await session.commit()
