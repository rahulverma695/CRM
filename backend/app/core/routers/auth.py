import re
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from app.core.models import Tenant, User
from app.crm.models import PipelineStage
from app.core.schemas.auth import SignupIn, LoginIn, TokenPair, UserOut, RefreshIn
from app.core.security.passwords import hash_password, verify_password
from app.core.security.jwt import create_access_token, create_refresh_token, decode_token
from app.core.middleware.tenant_context import set_tenant
from app.core.deps import get_current_claims, get_tenant_session
from app.database import get_session

async def _seed_default_stages(session, tenant_id) -> None:
    import uuid as _uuid
    defaults = [
        ("New Lead",  "#6b7280", 0),
        ("Contacted", "#3b82f6", 1),
        ("Qualified", "#8b5cf6", 2),
        ("Proposal",  "#f59e0b", 3),
        ("Won",       "#c6f24e", 4),
    ]
    for name, color, order in defaults:
        session.add(PipelineStage(
            id=_uuid.uuid4(), tenant_id=tenant_id,
            name=name, color=color, order=order, type="lead",
        ))


router = APIRouter(prefix="/auth", tags=["auth"])

# Precomputed hash used to equalize login timing for unknown/inactive users
# (prevents user-enumeration via response-time differences).
_DUMMY_PASSWORD_HASH = hash_password("dummy-password-for-constant-time-login")


def _slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "tenant"
    return f"{base}-{uuid.uuid4().hex[:6]}"


@router.post("/signup", response_model=TokenPair, status_code=201)
async def signup(body: SignupIn, session: Annotated[AsyncSession, Depends(get_session)]):
    tenant = Tenant(id=uuid.uuid4(), name=body.company_name, slug=_slugify(body.company_name))
    session.add(tenant)
    await session.flush()

    await set_tenant(session, str(tenant.id))
    await _seed_default_stages(session, tenant.id)
    user = User(
        id=uuid.uuid4(), tenant_id=tenant.id, email=str(body.email),
        name=body.name, role="admin", password_hash=hash_password(body.password),
    )
    session.add(user)
    await session.commit()

    return TokenPair(
        access_token=create_access_token(str(user.id), str(tenant.id), user.role),
        refresh_token=create_refresh_token(str(user.id), str(tenant.id), user.role),
    )


@router.post("/login", response_model=TokenPair)
async def login(body: LoginIn, session: Annotated[AsyncSession, Depends(get_session)]):
    result = await session.execute(
        text("SELECT id, tenant_id, role, password_hash, is_active "
             "FROM users WHERE email = :email"),
        {"email": str(body.email)},
    )
    row = result.first()
    valid_record = row is not None and row.is_active and bool(row.password_hash)
    hash_to_check = row.password_hash if valid_record else _DUMMY_PASSWORD_HASH
    password_ok = verify_password(body.password, hash_to_check)
    if not valid_record or not password_ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return TokenPair(
        access_token=create_access_token(str(row.id), str(row.tenant_id), row.role),
        refresh_token=create_refresh_token(str(row.id), str(row.tenant_id), row.role),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(body: RefreshIn):
    try:
        claims = decode_token(body.refresh_token)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    if claims.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not a refresh token")
    return TokenPair(
        access_token=create_access_token(claims["sub"], claims["tenant_id"], claims["role"]),
        refresh_token=create_refresh_token(claims["sub"], claims["tenant_id"], claims["role"]),
    )


@router.get("/me", response_model=UserOut)
async def me(
    claims: Annotated[dict, Depends(get_current_claims)],
    session: Annotated[AsyncSession, Depends(get_tenant_session)],
):
    user = (await session.execute(
        select(User).where(User.id == uuid.UUID(claims["sub"]))
    )).scalar_one_or_none()
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user
