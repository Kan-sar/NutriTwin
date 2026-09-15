from datetime import date
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from nutritwin_api.database import get_db
from nutritwin_api.models import Profile
from nutritwin_api.routers.core import _require_consent
from nutritwin_api.schemas import ConstructMealRequest
from nutritwin_api.security import CurrentUser
from nutritwin_api.services.construction import construct_demo_meal
from nutritwin_api.services.recommendations import recommend
from nutritwin_api.services.recompute import materialized_summary
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
    _profile(db, user.id)
    if effective_date > date.today():
        raise HTTPException(422, "future dates belong to simulations")
    return materialized_summary(db, user.id, effective_date)


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


@router.post("/recommendations/construct")
def construct_recommendation(
    payload: ConstructMealRequest,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    as_of: Annotated[date | None, Query()] = None,
) -> dict[str, Any]:
    effective_date = as_of or date.today()
    _require_consent(db, user.id)
    profile = _profile(db, user.id)
    try:
        snapshot = get_or_create_target_snapshot(db, user, profile, effective_date)
        if not payload.demo_mode and snapshot.provisional:
            raise HTTPException(
                409, "reviewed authoritative targets are required for real-data planning"
            )
        minimums = {} if payload.derive_from_gaps else dict(payload.nutrient_minimums)
        upper_limits: dict[str, Decimal] = {}
        if payload.derive_from_gaps or not payload.demo_mode:
            twin = build_twin_summary(db, user.id, snapshot, effective_date)
            for item in twin["nutrients"]:
                code = item["nutrient_code"]
                consumed = item["consumed"]["daily"]["total_amount"]
                amount = consumed if consumed is not None else Decimal("0")
                # Missing logs are unknown; real-data safety cannot assume nothing was eaten.
                if (
                    not payload.demo_mode
                    and not item["composition_complete_today"]
                    and (
                        item["target"]["rda"] is not None
                        or item["target"]["tul"] is not None
                        or code in minimums
                    )
                ):
                    raise HTTPException(
                        409, "complete logged composition required for upper-limit checks"
                    )
                if payload.derive_from_gaps and item["target"]["rda"] is not None:
                    gap = max(Decimal("0"), item["target"]["rda"] - amount)
                    if gap > 0:
                        minimums[code] = gap
                if item["target"]["tul"] is not None:
                    upper_limits[code] = max(Decimal("0"), item["target"]["tul"] - amount)
        return construct_demo_meal(
            db,
            user.id,
            profile,
            minimums,
            payload.maximum_budget_minor,
            effective_date,
            seed=payload.seed,
            time_limit_ms=payload.time_limit_ms,
            demo_mode=payload.demo_mode,
            maximum_preparation_minutes=payload.maximum_preparation_minutes,
            nutrient_maximums=upper_limits,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
