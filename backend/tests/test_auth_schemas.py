import pytest
from pydantic import ValidationError
from app.core.schemas.auth import SignupIn, LoginIn, TokenPair, UserOut


def test_signup_requires_valid_email():
    with pytest.raises(ValidationError):
        SignupIn(company_name="Acme", email="not-an-email", password="longenough", name="A")


def test_signup_rejects_short_password():
    with pytest.raises(ValidationError):
        SignupIn(company_name="Acme", email="a@b.com", password="short", name="A")


def test_token_pair_shape():
    tp = TokenPair(access_token="a", refresh_token="r")
    assert tp.token_type == "bearer"
