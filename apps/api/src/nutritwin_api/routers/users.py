from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from nutritwin_api.database import get_db
from nutritwin_api.models import ConsentRecord
from nutritwin_api.schemas import ConsentRequest, ConsentResponse, UserPublic
from nutritwin_api.security import CurrentUser

router = APIRouter(prefix="/api/v1", tags=["users"])


@router.get("/users/me", response_model=UserPublic)
def me(user: CurrentUser) -> UserPublic:
    return UserPublic(id=user.id, email=user.email_normalized, role=user.role)


@router.post("/consents", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
def record_consent(
    payload: ConsentRequest,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ConsentRecord:
    record = ConsentRecord(user_id=user.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
