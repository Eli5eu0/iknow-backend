from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deletion_requested_at: datetime | None = None
    deletion_scheduled_at: datetime | None = None


class UserUpdate(BaseModel):
    # Email and role are intentionally not writable through USERS.
    model_config = ConfigDict(extra="forbid")


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class AccountRecovery(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=1, max_length=128)
