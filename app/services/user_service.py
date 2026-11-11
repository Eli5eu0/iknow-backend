from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import RefreshToken, User


RECOVERY_DAYS = 30


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    if verify_password(new_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different")
    user.password_hash = hash_password(new_password)
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(timezone.utc))
    )
    db.commit()


def request_deactivation(db: Session, user: User) -> None:
    now = datetime.now(timezone.utc)
    user.is_active = False
    user.deletion_requested_at = now
    user.deletion_scheduled_at = now + timedelta(days=RECOVERY_DAYS)
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    db.commit()


def recover_account(db: Session, user: User) -> None:
    now = datetime.now(timezone.utc)
    scheduled = user.deletion_scheduled_at
    if scheduled is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No pending account deletion")
    if scheduled.tzinfo is None:
        scheduled = scheduled.replace(tzinfo=timezone.utc)
    if scheduled <= now:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Account recovery period has expired")
    user.is_active = True
    user.deletion_requested_at = None
    user.deletion_scheduled_at = None
    db.commit()
