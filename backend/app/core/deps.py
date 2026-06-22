from typing import Annotated
from fastapi import Depends, Header, HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security.jwt import decode_token
from app.core.middleware.tenant_context import set_tenant
from app.database import get_session


def claims_from_authorization(authorization: str | None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        claims = decode_token(token)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    if claims.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not an access token")
    return claims


async def get_current_claims(authorization: Annotated[str | None, Header()] = None) -> dict:
    return claims_from_authorization(authorization)


async def get_tenant_session(
    claims: Annotated[dict, Depends(get_current_claims)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncSession:
    """Return a session with the RLS tenant context already applied.

    Cleanup is handled by get_session's generator dependency.
    """
    tenant_id = claims.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Malformed token: missing tenant_id")
    await set_tenant(session, tenant_id)
    return session


def require_role(claims: dict, role: str) -> None:
    if claims.get("role") != role:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")


async def require_admin(claims: Annotated[dict, Depends(get_current_claims)]) -> dict:
    require_role(claims, "admin")
    return claims
