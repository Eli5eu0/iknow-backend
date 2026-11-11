from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest
from app.schemas.user import AccountRecovery, PasswordChange, UserRead
from app.services.user_service import change_password, recover_account, request_deactivation

router = APIRouter(prefix="/users")


@router.get("/me", response_model=UserRead)
def read_my_account(user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def update_my_password(
    payload: PasswordChange,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    change_password(db, user, payload.current_password, payload.new_password)
    return None


@router.delete("/me", status_code=status.HTTP_202_ACCEPTED)
def deactivate_my_account(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request_deactivation(db, user)
    return {
        "detail": "Account deactivated; recovery is available for 30 days",
        "deletion_scheduled_at": user.deletion_scheduled_at,
    }


@router.post("/recover", response_model=UserRead)
def recover_my_account(
    payload: AccountRecovery,
    db: Session = Depends(get_db),
) -> UserRead:
    normalized_email = payload.email.strip().lower()
    user = db.scalar(select(User).where(User.email == normalized_email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if user.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account is already active")
    recover_account(db, user)
    return UserRead.model_validate(user)
