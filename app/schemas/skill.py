from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.pagination import Pagination


class SkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str
    category: str | None


class SkillSortField(str, Enum):
    NAME = "name"


class SkillListResponse(BaseModel):
    items: list[SkillRead]
    pagination: Pagination
