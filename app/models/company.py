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


# Campos que têm de estar preenchidos para o perfil empresarial estar completo (D07).
# A ordem é a devolvida em `missing_fields`.
PROFILE_REQUIRED_FIELDS = ("name", "legal_name", "tax_id", "description", "city", "country")


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    # Anulável: a linha é criada vazia no registo e o perfil é preenchido depois.
    name: Mapped[str | None] = mapped_column(String(180))
    legal_name: Mapped[str | None] = mapped_column(String(220))
    tax_id: Mapped[str | None] = mapped_column(String(80), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    verification_status: Mapped[CompanyVerificationStatus] = mapped_column(
        Enum(
            CompanyVerificationStatus,
            native_enum=False,
            create_constraint=True,
            length=24,
            name="companyverificationstatus",
        ),
        default=CompanyVerificationStatus.NOT_SUBMITTED,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    @property
    def missing_fields(self) -> list[str]:
        return [field for field in PROFILE_REQUIRED_FIELDS if not (getattr(self, field) or "").strip()]

    @property
    def profile_completed(self) -> bool:
        return not self.missing_fields

    @property
    def is_verified(self) -> bool:
        return self.verification_status == CompanyVerificationStatus.VERIFIED

    user: Mapped["User"] = relationship("User", back_populates="company")
    opportunities: Mapped[list["Opportunity"]] = relationship(
        "Opportunity", back_populates="company", cascade="all, delete-orphan"
    )
