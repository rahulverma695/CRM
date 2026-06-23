# backend/app/crm/schemas.py
from __future__ import annotations
import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


# ── Pipeline Stages ──────────────────────────────────────────────────────────

class StageIn(BaseModel):
    name: str
    color: str = "#c6f24e"
    order: int = 0
    type: str = "lead"


class StagePatch(BaseModel):
    name: str | None = None
    color: str | None = None
    order: int | None = None
    type: str | None = None


class StageOut(BaseModel):
    id: uuid.UUID
    name: str
    color: str
    order: int
    type: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Leads ────────────────────────────────────────────────────────────────────

class LeadIn(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    stage_id: uuid.UUID | None = None
    owner_id: uuid.UUID | None = None
    source: str | None = None


class LeadPatch(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    stage_id: uuid.UUID | None = None
    owner_id: uuid.UUID | None = None
    source: str | None = None


class LeadOut(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    company: str | None
    stage_id: uuid.UUID | None
    owner_id: uuid.UUID | None
    source: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Deals ────────────────────────────────────────────────────────────────────

class DealIn(BaseModel):
    title: str
    lead_id: uuid.UUID | None = None
    value: float | None = None
    currency: str = "USD"
    stage_id: uuid.UUID | None = None
    probability: int | None = None
    expected_close_date: date | None = None


class DealPatch(BaseModel):
    title: str | None = None
    lead_id: uuid.UUID | None = None
    value: float | None = None
    currency: str | None = None
    stage_id: uuid.UUID | None = None
    probability: int | None = None
    expected_close_date: date | None = None


class DealOut(BaseModel):
    id: uuid.UUID
    title: str
    lead_id: uuid.UUID | None
    value: float | None
    currency: str
    stage_id: uuid.UUID | None
    probability: int | None
    expected_close_date: date | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Activities ───────────────────────────────────────────────────────────────

class ActivityIn(BaseModel):
    lead_id: uuid.UUID | None = None
    deal_id: uuid.UUID | None = None
    type: str  # "note"|"task"|"email"|"stage_change"
    content: dict[str, Any] = {}


class ActivityOut(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID | None
    deal_id: uuid.UUID | None
    type: str
    content: dict[str, Any]
    created_by: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── CRM Tasks ────────────────────────────────────────────────────────────────

class CrmTaskIn(BaseModel):
    title: str
    lead_id: uuid.UUID | None = None
    deal_id: uuid.UUID | None = None
    due_date: date | None = None
    assignee_id: uuid.UUID | None = None


class CrmTaskPatch(BaseModel):
    title: str | None = None
    due_date: date | None = None
    assignee_id: uuid.UUID | None = None
    status: str | None = None


class CrmTaskOut(BaseModel):
    id: uuid.UUID
    lead_id: uuid.UUID | None
    deal_id: uuid.UUID | None
    title: str
    due_date: date | None
    assignee_id: uuid.UUID | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Custom Views ─────────────────────────────────────────────────────────────

class CustomViewIn(BaseModel):
    name: str
    filters: dict[str, Any] = {}
    sort: str | None = None
    columns: list[str] = []
    is_shared: bool = False


class CustomViewPatch(BaseModel):
    name: str | None = None
    filters: dict[str, Any] | None = None
    sort: str | None = None
    columns: list[str] | None = None
    is_shared: bool | None = None


class CustomViewOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    filters: dict[str, Any]
    sort: str | None
    columns: list[str]
    is_shared: bool
    created_at: datetime

    model_config = {"from_attributes": True}
