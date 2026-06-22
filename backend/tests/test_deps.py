import uuid
import pytest
from fastapi import HTTPException
from app.core.deps import claims_from_authorization, require_role
from app.core.security.jwt import create_access_token, create_refresh_token


def test_claims_from_valid_bearer():
    uid, tid = str(uuid.uuid4()), str(uuid.uuid4())
    token = create_access_token(user_id=uid, tenant_id=tid, role="member")
    claims = claims_from_authorization(f"Bearer {token}")
    assert claims["sub"] == uid


def test_claims_rejects_missing_header():
    with pytest.raises(HTTPException) as exc:
        claims_from_authorization(None)
    assert exc.value.status_code == 401


def test_claims_rejects_refresh_token_for_access():
    token = create_refresh_token(user_id="u", tenant_id="t", role="member")
    with pytest.raises(HTTPException) as exc:
        claims_from_authorization(f"Bearer {token}")
    assert exc.value.status_code == 401


def test_require_role_allows_admin():
    require_role({"role": "admin"}, "admin")  # no raise


def test_require_role_blocks_member():
    with pytest.raises(HTTPException) as exc:
        require_role({"role": "member"}, "admin")
    assert exc.value.status_code == 403
