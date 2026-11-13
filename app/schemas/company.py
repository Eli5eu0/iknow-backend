from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.company import PROFILE_REQUIRED_FIELDS, CompanyVerificationStatus

ProfileField = Literal["name", "legal_name", "tax_id", "description", "city", "country"]


class CompanyUpdate(BaseModel):
    """Actualização parcial: só os campos enviados mudam; verification_status não é editável."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=180)
    legal_name: str | None = Field(default=None, min_length=1, max_length=220)
    tax_id: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = Field(default=None, min_length=1, max_length=5000)
    website: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    country: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator(*PROFILE_REQUIRED_FIELDS, mode="before")
    @classmethod
    def reject_null_required_fields(cls, value):
        if value is None:
            raise ValueError("Field cannot be null")
        return value

    @field_validator("website")
    @classmethod
    def validate_website(cls, value: str | None) -> str | None:
        if value is None:
            return None
        lowered = value.lower()
        scheme = next((s for s in ("http://", "https://") if lowered.startswith(s)), None)
        if scheme is None or len(value) == len(scheme) or any(ch.isspace() for ch in value):
            raise ValueError("Website must be a valid http:// or https:// URL")
        return value


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str | None
    legal_name: str | None
    tax_id: str | None
    description: str | None
    website: str | None
    city: str | None
    country: str | None
    verification_status: CompanyVerificationStatus
    profile_completed: bool
    missing_fields: list[ProfileField]
    created_at: datetime
    updated_at: datetime


class CompanyPublicRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    website: str | None
    city: str | None
    country: str | None
    is_verified: bool
