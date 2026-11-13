from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.user import User


def get_company_for_user(db: Session, user: User) -> Company:
    company = db.scalar(select(Company).where(Company.user_id == user.id))
    if company is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company profile not found")
    return company


def update_company(db: Session, user: User, data: dict) -> Company:
    company = get_company_for_user(db, user)

    tax_id = data.get("tax_id")
    if tax_id is not None and tax_id != company.tax_id:
        taken = db.scalar(select(Company.id).where(Company.tax_id == tax_id, Company.id != company.id))
        if taken is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tax ID already registered")

    for key, value in data.items():
        setattr(company, key, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        # Conflito simultâneo no tax_id: a unicidade é garantida pela base de dados.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Tax ID already registered"
        ) from exc
    db.refresh(company)
    return company


def get_public_company(db: Session, company_id: UUID) -> Company:
    """Perfil público: só empresas com perfil completo e conta activa."""
    company = db.scalar(
        select(Company)
        .join(User, User.id == Company.user_id)
        .where(Company.id == company_id, User.is_active.is_(True))
    )
    if company is None or not company.profile_completed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company
