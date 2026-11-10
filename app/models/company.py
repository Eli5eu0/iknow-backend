from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base


class CompanyVerificationStatus(str, enum.Enum):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(220))
    tax_id: Mapped[str | None] = mapped_column(String(80), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    verification_status: Mapped[CompanyVerificationStatus] = mapped_column(
        Enum(CompanyVerificationStatus, native_enum=False, length=24),
        default=CompanyVerificationStatus.NOT_SUBMITTED,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="company")
    opportunities: Mapped[list[Opportunity]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
