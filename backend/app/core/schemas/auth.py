import uuid
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class SignupIn(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: EmailStr
    name: str
    role: str
    avatar_url: str | None = None


class InviteIn(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=255)
    role: str = Field(default="member", pattern="^(admin|member)$")


class AcceptInviteIn(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)
