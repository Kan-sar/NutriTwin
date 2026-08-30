from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nutritwin_api.config import Settings
from nutritwin_api.database import get_db
from nutritwin_api.models import RefreshSession, User, utc_now
from nutritwin_api.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)
from nutritwin_api.security import (
    create_access_token,
    create_refresh_session,
    hash_password,
    normalize_email,
    revoke_refresh_family,
    token_digest,
    verify_password,
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


def _public(user: User) -> UserPublic:
    return UserPublic(id=user.id, email=user.email_normalized, role=user.role)


def _tokens(db: Session, user: User, settings: Settings) -> TokenResponse:
    access, expires_in = create_access_token(user, settings)
    refresh, record = create_refresh_session(user, settings)
    db.add(record)
    db.commit()
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=expires_in,
    )


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> UserPublic:
    user = User(
        email_normalized=normalize_email(str(payload.email)),
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="account already exists") from exc
    db.refresh(user)
    return _public(user)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    user = db.scalar(
        select(User).where(User.email_normalized == normalize_email(str(payload.email)))
    )
    if (
        user is None
        or not user.is_active
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(status_code=401, detail="invalid email or password")
    return _tokens(db, user, request.app.state.settings)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    payload: RefreshRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    record = db.scalar(
        select(RefreshSession).where(
            RefreshSession.token_hash == token_digest(payload.refresh_token)
        )
    )
    if record is None:
        raise HTTPException(status_code=401, detail="invalid refresh token")
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if record.revoked_at is not None:
        revoke_refresh_family(db, record.family_id)
        db.commit()
        raise HTTPException(status_code=401, detail="refresh token reuse detected")
    if expires_at <= datetime.now(UTC):
        record.revoked_at = utc_now()
        db.commit()
        raise HTTPException(status_code=401, detail="refresh token expired")
    user = db.get(User, record.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="invalid refresh token")
    settings: Settings = request.app.state.settings
    raw, replacement = create_refresh_session(user, settings, family_id=record.family_id)
    db.add(replacement)
    db.flush()
    record.revoked_at = utc_now()
    record.replaced_by_id = replacement.id
    access, expires_in = create_access_token(user, settings)
    db.commit()
    return TokenResponse(access_token=access, refresh_token=raw, expires_in=expires_in)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Annotated[Session, Depends(get_db)]) -> None:
    record = db.scalar(
        select(RefreshSession).where(
            RefreshSession.token_hash == token_digest(payload.refresh_token)
        )
    )
    if record is not None and record.revoked_at is None:
        record.revoked_at = utc_now()
        db.commit()
