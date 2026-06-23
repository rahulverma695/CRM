import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.integrations.starlette_client import OAuth
from app.config import settings
from app.core.security.jwt import create_access_token, create_refresh_token
from app.database import get_session

router = APIRouter(prefix="/auth/google", tags=["oauth"])

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


async def resolve_google_email(request: Request) -> str:
    """Real resolver: exchange the callback for a token and return the email.
    Overridable in tests via app.dependency_overrides."""
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if not userinfo or not userinfo.get("email"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No email from Google")
    return userinfo["email"]


@router.get("/login")
async def google_login(request: Request):
    return await oauth.google.authorize_redirect(request, settings.google_redirect_uri)


@router.get("/callback")
async def google_callback(
    email: Annotated[str, Depends(resolve_google_email)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    row = (await session.execute(
        text("SELECT id, tenant_id, role FROM users WHERE email = :e AND is_active = true"),
        {"e": email},
    )).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                           "No account for this Google email — sign up first")
    access = create_access_token(str(row.id), str(row.tenant_id), row.role)
    refresh = create_refresh_token(str(row.id), str(row.tenant_id), row.role)
    return RedirectResponse(
        f"{settings.frontend_url}/auth/callback#access={access}&refresh={refresh}"
    )
