from __future__ import annotations
import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models.base import Base, TimestampMixin, TenantMixin


class PipelineStage(Base, TimestampMixin, TenantMixin):
    __tablename__ = "pipeline_stages"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100))
    color: Mapped[str] = mapped_column(String(20), default="#c6f24e")
    order: Mapped[int] = mapped_column(Integer, default=0)
    type: Mapped[str] = mapped_column(String(10), default="lead")  # "lead" | "deal"


class Lead(Base, TimestampMixin, TenantMixin):
    __tablename__ = "leads"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    company: Mapped[str | None] = mapped_column(String(200))
    stage_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("pipeline_stages.id", ondelete="SET NULL"))
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    source: Mapped[str | None] = mapped_column(String(100))


class Deal(Base, TimestampMixin, TenantMixin):
    __tablename__ = "deals"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("leads.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(200))
    value: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    stage_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("pipeline_stages.id", ondelete="SET NULL"))
    probability: Mapped[int | None] = mapped_column(Integer)
    expected_close_date: Mapped[date | None] = mapped_column(Date)


class Activity(Base, TimestampMixin, TenantMixin):
    __tablename__ = "activities"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"))
    deal_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("deals.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(20))  # "note"|"task"|"email"|"stage_change"
    content: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))


class CrmTask(Base, TimestampMixin, TenantMixin):
    __tablename__ = "crm_tasks"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"))
    deal_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("deals.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(300))
    due_date: Mapped[date | None] = mapped_column(Date)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(10), default="open")  # "open"|"done"


class CustomView(Base, TimestampMixin, TenantMixin):
    __tablename__ = "custom_views"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    filters: Mapped[dict] = mapped_column(JSONB, default=dict)
    sort: Mapped[str | None] = mapped_column(String(100))
    columns: Mapped[list] = mapped_column(JSONB, default=list)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)
