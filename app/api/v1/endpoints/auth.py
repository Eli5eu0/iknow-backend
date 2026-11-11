from datetime import datetime, timedelta, timezone
import hmac
from urllib.parse import urlsplit
from uuid import uuid4

import jwt
from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import (
    create_access_token,
    derive_csrf_token,
    generate_opaque_token,
    hash_password,
    hash_token,
    password_needs_rehash,
    verify_password,
)
from app.db.session import get_db
from app.models.user import RefreshToken, User
from app.schemas.auth import AuthResponse, CsrfResponse, LoginRequest, RegisterRequest, UserPublic

router = APIRouter(prefix="/auth")
REFRESH_COOKIE_NAME = "iknow_refresh"


def _cookie_path() -> str:
    return f"{settings.api_v1_prefix.rstrip('/')}/auth"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path=_cookie_path(),
        domain=settings.auth_cookie_domain,
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite=settings.auth_cookie_samesite,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=_cookie_path(),
        domain=settings.auth_cookie_domain,
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite=settings.auth_cookie_samesite,
    )


def _ensure_trusted_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if not origin:
        referer = request.headers.get("referer")
        if referer:
            parsed = urlsplit(referer)
            origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else None
    if not origin or origin.rstrip("/") not in settings.cors_origin_list:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Untrusted request origin",
        )


def _new_refresh_session(db: Session, user: User, family_id=None) -> tuple[str, str]:
    refresh_value = generate_opaque_token()
    now = datetime.now(timezone.utc)
    token_row = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_value),
        family_id=family_id or uuid4(),
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(token_row)
    db.flush()
    csrf_value = derive_csrf_token(token_row.id)
    token_row.csrf_token_hash = hash_token(csrf_value)
    db.flush()
    return refresh_value, csrf_value


def _auth_response(user: User, csrf_token: str) -> AuthResponse:
    return AuthResponse(
        access_token=create_access_token(user.id, user.role.value),
        expires_in=settings.access_token_expire_minutes * 60,
        csrf_token=csrf_token,
        user=UserPublic.model_validate(user),
    )


def _revoke_family(db: Session, family_id) -> None:
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(timezone.utc))
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    _ensure_trusted_origin(request)
    if db.scalar(select(User.id).where(User.email == payload.email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(email=payload.email, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    try:
        db.flush()
        refresh_value, csrf_value = _new_refresh_session(db, user)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered") from exc

    _set_refresh_cookie(response, refresh_value)
    return _auth_response(user, csrf_value)


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    _ensure_trusted_origin(request)
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(payload.password)

    refresh_value, csrf_value = _new_refresh_session(db, user)
    db.commit()
    _set_refresh_cookie(response, refresh_value)
    return _auth_response(user, csrf_value)


@router.get("/csrf", response_model=CsrfResponse)
def issue_csrf_token(
    request: Request,
    db: Session = Depends(get_db),
) -> CsrfResponse:
    _ensure_trusted_origin(request)
    raw_refresh = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session not found")

    token_row = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == hash_token(raw_refresh))
        .with_for_update()
    )
    now = datetime.now(timezone.utc)
    if token_row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh session")
    expires_at = token_row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if token_row.revoked_at is not None or expires_at <= now:
        if token_row.revoked_at is not None or expires_at <= now:
            _revoke_family(db, token_row.family_id)
            db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session is invalid")

    csrf_value = derive_csrf_token(token_row.id)
    if not token_row.csrf_token_hash or not hmac.compare_digest(
        hash_token(csrf_value), token_row.csrf_token_hash
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid CSRF session")
    return CsrfResponse(csrf_token=csrf_value)


@router.post("/refresh", response_model=AuthResponse)
def refresh(
    request: Request,
    response: Response,
    csrf_header: str | None = Header(default=None, alias="X-CSRF-Token"),
    db: Session = Depends(get_db),
) -> AuthResponse:
    _ensure_trusted_origin(request)
    raw_refresh = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session not found")

    token_row = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == hash_token(raw_refresh))
        .with_for_update()
    )
    if token_row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh session")

    if token_row.revoked_at is not None:
        _revoke_family(db, token_row.family_id)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token reuse detected")

    now = datetime.now(timezone.utc)
    expires_at = token_row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        _revoke_family(db, token_row.family_id)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh session expired")

    expected_csrf_hash = token_row.csrf_token_hash
    if not csrf_header or not expected_csrf_hash or not hmac.compare_digest(
        hash_token(csrf_header), expected_csrf_hash
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")

    user = db.get(User, token_row.user_id)
    if user is None or not user.is_active:
        _revoke_family(db, token_row.family_id)
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive")

    token_row.revoked_at = now
    next_refresh, next_csrf = _new_refresh_session(db, user, token_row.family_id)
    next_row = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(next_refresh))
    )
    token_row.replaced_by_id = next_row.id
    db.commit()

    _set_refresh_cookie(response, next_refresh)
    return _auth_response(user, next_csrf)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    csrf_header: str | None = Header(default=None, alias="X-CSRF-Token"),
    db: Session = Depends(get_db),
) -> Response:
    _ensure_trusted_origin(request)
    raw_refresh = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_refresh:
        token_row = db.scalar(
            select(RefreshToken)
            .where(RefreshToken.token_hash == hash_token(raw_refresh))
            .with_for_update()
        )
        csrf_header = request.headers.get("X-CSRF-Token")
        if token_row is not None and token_row.revoked_at is None:
            expected = token_row.csrf_token_hash
            if not csrf_header or not expected or not hmac.compare_digest(hash_token(csrf_header), expected):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")
            _revoke_family(db, token_row.family_id)
            db.commit()
    _clear_refresh_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserPublic)
def get_me(user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic.model_validate(user)
