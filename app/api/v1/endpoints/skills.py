from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.pagination import PageParams, SortOrder, build_pagination
from app.schemas.skill import SkillListResponse, SkillRead, SkillSortField
from app.services import skill_service

router = APIRouter(prefix="/skills", dependencies=[Depends(get_current_user)])


@router.get("", response_model=SkillListResponse)
def list_skills(
    params: PageParams = Depends(),
    q: str | None = Query(default=None, min_length=1, max_length=100),
    category: str | None = Query(default=None, min_length=1, max_length=80),
    sort_by: SkillSortField = Query(default=SkillSortField.NAME),
    sort_order: SortOrder = Query(default=SortOrder.ASC),
    db: Session = Depends(get_db),
) -> SkillListResponse:
    items, total_items = skill_service.list_skills(db, params, q, category, sort_by, sort_order)
    return SkillListResponse(
        items=[SkillRead.model_validate(item) for item in items],
        pagination=build_pagination(params, total_items),
    )


@router.get("/{skill_id}", response_model=SkillRead)
def read_skill(skill_id: UUID, db: Session = Depends(get_db)) -> SkillRead:
    return SkillRead.model_validate(skill_service.get_skill(db, skill_id))
