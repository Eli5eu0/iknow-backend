from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base


class OpportunityStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[OpportunityStatus] = mapped_column(
        Enum(OpportunityStatus, native_enum=False, length=16),
        default=OpportunityStatus.DRAFT,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    company: Mapped[Company] = relationship(back_populates="opportunities")
    skills: Mapped[list[OpportunitySkill]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan"
    )


class OpportunitySkill(Base):
    __tablename__ = "opportunity_skills"

    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    opportunity: Mapped[Opportunity] = relationship(back_populates="skills")
    skill: Mapped[Skill] = relationship(back_populates="opportunity_links")
