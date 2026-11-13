from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.company import CompanyPublicRead, CompanyRead, CompanyUpdate
from app.services import company_service

router = APIRouter(prefix="/companies")


# As rotas /me têm de ser declaradas antes de /{company_id}.
@router.get("/me", response_model=CompanyRead)
def read_my_company(
    user: User = Depends(require_roles(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyRead:
    return CompanyRead.model_validate(company_service.get_company_for_user(db, user))


@router.patch("/me", response_model=CompanyRead)
def update_my_company(
    payload: CompanyUpdate,
    user: User = Depends(require_roles(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyRead:
    company = company_service.update_company(db, user, payload.model_dump(exclude_unset=True))
    return CompanyRead.model_validate(company)


@router.get("/{company_id}", response_model=CompanyPublicRead, dependencies=[Depends(get_current_user)])
def read_public_company(company_id: UUID, db: Session = Depends(get_db)) -> CompanyPublicRead:
    return CompanyPublicRead.model_validate(company_service.get_public_company(db, company_id))
