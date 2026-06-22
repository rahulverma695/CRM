from datetime import datetime, timedelta, timezone
from jose import jwt
from app.config import settings

ALGORITHM = "HS256"


def _create_token(user_id: str, tenant_id: str, role: str, token_type: str, expires: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + expires,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def create_access_token(user_id: str, tenant_id: str, role: str) -> str:
    return _create_token(user_id, tenant_id, role, "access",
                         timedelta(minutes=settings.access_token_minutes))


def create_refresh_token(user_id: str, tenant_id: str, role: str) -> str:
    return _create_token(user_id, tenant_id, role, "refresh",
                         timedelta(days=settings.refresh_token_days))


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
