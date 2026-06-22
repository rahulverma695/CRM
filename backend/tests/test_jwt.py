import uuid
import pytest
from jose import JWTError
from app.core.security.jwt import create_access_token, create_refresh_token, decode_token


def test_access_token_roundtrip():
    uid, tid = str(uuid.uuid4()), str(uuid.uuid4())
    token = create_access_token(user_id=uid, tenant_id=tid, role="admin")
    claims = decode_token(token)
    assert claims["sub"] == uid
    assert claims["tenant_id"] == tid
    assert claims["role"] == "admin"
    assert claims["type"] == "access"


def test_refresh_token_has_type_refresh():
    token = create_refresh_token(user_id="u1", tenant_id="t1", role="member")
    claims = decode_token(token)
    assert claims["type"] == "refresh"


def test_decode_rejects_garbage():
    with pytest.raises(JWTError):
        decode_token("not.a.token")
