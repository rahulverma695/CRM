import uuid
from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt, JWTError
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.core.models import User
from app.core.schemas.auth import InviteIn, AcceptInviteIn, TokenPair, UserOut
from app.core.security.passwords import hash_password
from app.core.security.jwt import create_access_token, create_refresh_token, ALGORITHM
from app.core.deps import require_admin, get_tenant_session
from app.core.email import get_email_sender, EmailSender
from app.database import get_session

router = APIRouter(prefix="/invites", tags=["invites"])


def _make_invite_token(user_id: str, tenant_id: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": user_id, "tenant_id": tenant_id, "type": "invite",
         "iat": now, "exp": now + timedelta(days=7)},
        settings.jwt_secret, algorithm=ALGORITHM,
    )


@router.post("", response_model=UserOut, status_code=201)
async def create_invite(
    body: InviteIn,
    admin: Annotated[dict, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_tenant_session)],
    sender: Annotated[EmailSender, Depends(get_email_sender)],
):
    tenant_id = admin["tenant_id"]
    existing = (await session.execute(
        select(User).where(User.email == str(body.email))
    )).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "A user with this email already exists")
    user = User(
        id=uuid.uuid4(), tenant_id=uuid.UUID(tenant_id), email=str(body.email),
        name=body.name, role=body.role, is_active=False, password_hash=None,
    )
    session.add(user)
    await session.commit()

    token = _make_invite_token(str(user.id), tenant_id)
    link = f"{settings.frontend_url}/accept-invite?token={token}"
    await sender.send(str(body.email), "You're invited", f"Accept here: {link}")
    return user


@router.post("/accept", response_model=TokenPair)
async def accept_invite(
    body: AcceptInviteIn,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    try:
        claims = jwt.decode(body.token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid invite")
    if claims.get("type") != "invite":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not an invite token")

    await session.execute(
        text("SELECT set_config('app.tenant_id', :t, true)"),
        {"t": claims["tenant_id"]},
    )
    user = (await session.execute(
        select(User).where(User.id == uuid.UUID(claims["sub"]))
    )).scalar_one_or_none()
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite target missing")
    if user.is_active:
        raise HTTPException(status.HTTP_409_CONFLICT, "Invite already accepted")
    user.password_hash = hash_password(body.password)
    user.is_active = True
    await session.commit()

    return TokenPair(
        access_token=create_access_token(str(user.id), str(user.tenant_id), user.role),
        refresh_token=create_refresh_token(str(user.id), str(user.tenant_id), user.role),
    )
