from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.schemas.pagination import PageParams, SortOrder
from app.schemas.skill import SkillSortField

_SORT_COLUMNS = {SkillSortField.NAME: Skill.name}


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def list_skills(
    db: Session,
    params: PageParams,
    q: str | None,
    category: str | None,
    sort_by: SkillSortField,
    sort_order: SortOrder,
) -> tuple[list[Skill], int]:
    filters = []
    if q is not None:
        filters.append(Skill.name.ilike(f"%{_escape_like(q)}%", escape="\\"))
    if category is not None:
        filters.append(Skill.category == category)

    total_items = db.scalar(select(func.count()).select_from(Skill).where(*filters)) or 0

    column = _SORT_COLUMNS[sort_by]
    ordering = column.desc() if sort_order is SortOrder.DESC else column.asc()
    items = db.scalars(
        select(Skill).where(*filters).order_by(ordering).offset(params.offset).limit(params.page_size)
    ).all()
    return list(items), total_items


def get_skill(db: Session, skill_id: UUID) -> Skill:
    skill = db.get(Skill, skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill
