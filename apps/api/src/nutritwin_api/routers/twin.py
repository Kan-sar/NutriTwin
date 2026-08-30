from datetime import date
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from nutritwin_api.database import get_db
from nutritwin_api.models import Profile
from nutritwin_api.routers.core import _require_consent
from nutritwin_api.security import CurrentUser
from nutritwin_api.services.recommendations import recommend
from nutritwin_api.services.targets import get_or_create_target_snapshot
from nutritwin_api.services.twin import build_twin_summary

router = APIRouter(prefix="/api/v1", tags=["digital twin"])


def _profile(db: Session, user_id: object) -> Profile:
    profile = db.scalar(select(Profile).where(Profile.user_id == user_id))
    if profile is None:
        raise HTTPException(status_code=404, detail="profile not found")
    return profile


@router.get("/twin/summary")
def summary(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    as_of: Annotated[date | None, Query()] = None,
) -> dict[str, Any]:
    effective_date = as_of or date.today()
    _require_consent(db, user.id)
    profile = _profile(db, user.id)
    snapshot = get_or_create_target_snapshot(db, user, profile, effective_date)
    return build_twin_summary(db, user.id, snapshot, effective_date)


@router.get("/recommendations")
def recommendations(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    as_of: Annotated[date | None, Query()] = None,
) -> dict[str, Any]:
    effective_date = as_of or date.today()
    _require_consent(db, user.id)
    profile = _profile(db, user.id)
    snapshot = get_or_create_target_snapshot(db, user, profile, effective_date)
    targets = {
        value.nutrient.code: value.rda
        for value in snapshot.values
        if isinstance(value.rda, Decimal)
    }
    ranked = recommend(db, user.id, profile, targets, effective_date)
    return {
        "as_of_date": effective_date,
        "model_version": "weighted-ranking-v1",
        "recommendations": [item for item in ranked if item["accepted"]],
        "rejected_candidates": [item for item in ranked if not item["accepted"]],
        "notice": "Demo meals and nutrient values are synthetic; this is not dietary advice.",
        "llm_used": False,
    }
