"""Password hashing, JWT access tokens, opaque refresh tokens, and RBAC dependencies."""

import hashlib
import secrets
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from nutritwin_api.config import Settings
from nutritwin_api.database import get_db
from nutritwin_api.models import RefreshSession, Role, User, utc_now

password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def token_digest(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_access_token(user: User, settings: Settings) -> tuple[str, int]:
    now = datetime.now(UTC)
    expires = now + timedelta(minutes=settings.access_token_minutes)
    claims = {
        "sub": str(user.id),
        "role": user.role.value,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": expires,
        "iss": "nutritwin-local",
    }
    encoded = jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded, int((expires - now).total_seconds())


def create_refresh_session(
    user: User,
    settings: Settings,
    *,
    family_id: uuid.UUID | None = None,
) -> tuple[str, RefreshSession]:
    raw = secrets.token_urlsafe(48)
    record = RefreshSession(
        user_id=user.id,
        family_id=family_id or uuid.uuid4(),
        token_hash=token_digest(raw),
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
    )
    return raw, record


def revoke_refresh_family(db: Session, family_id: uuid.UUID) -> None:
    db.execute(
        update(RefreshSession)
        .where(RefreshSession.family_id == family_id, RefreshSession.revoked_at.is_(None))
        .values(revoked_at=utc_now())
    )


def _auth_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid or expired authentication",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None:
        raise _auth_error()
    settings: Settings = request.app.state.settings
    try:
        claims = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer="nutritwin-local",
        )
        if claims.get("type") != "access":
            raise _auth_error()
        user_id = uuid.UUID(claims["sub"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
        raise _auth_error() from exc
    user = db.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))
    if user is None or claims.get("role") != user.role.value:
        raise _auth_error()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: Role) -> Callable[[CurrentUser], User]:
    allowed = set(roles)

    def dependency(user: CurrentUser) -> User:
        if user.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        return user

    return dependency
