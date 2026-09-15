"""Owner-scoped preference, manual-price and decision-history surfaces."""

from datetime import date
from decimal import Decimal
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from nutritwin_api.database import get_db
from nutritwin_api.models import Food, FoodOffer, RecommendationDecision, RecommendationPreference
from nutritwin_api.routers.core import _require_consent
from nutritwin_api.security import CurrentUser

router = APIRouter(prefix="/api/v1", tags=["meal planning"])


class Preferences(BaseModel):
    weights: dict[str, Decimal] = Field(
        default_factory=lambda: {
            "gap_coverage": Decimal("0.7"),
            "preparation_time": Decimal("0.2"),
            "variety": Decimal("0.1"),
        },
        max_length=3,
    )
    maximum_budget_minor: int | None = Field(default=None, ge=0, le=100000)
    maximum_preparation_minutes: int = Field(default=45, ge=1, le=240)

    @field_validator("weights")
    @classmethod
    def valid_weights(cls, values: dict[str, Decimal]) -> dict[str, Decimal]:
        if not values or not set(values) <= {"gap_coverage", "preparation_time", "variety"}:
            raise ValueError("only supported, measured objectives can be weighted")
        if any(not v.is_finite() or v < 0 or v > 100 for v in values.values()):
            raise ValueError("weights must be finite and nonnegative")
        if sum(values.values()) <= 0:
            raise ValueError("at least one weight must be positive")
        return values


@router.get("/preferences")
def get_preferences(user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> Preferences:
    row = db.get(RecommendationPreference, user.id)
    if row is not None:
        return Preferences.model_validate(row.settings)
    return Preferences(maximum_preparation_minutes=30 if user.role.value == "student" else 45)


@router.put("/preferences")
def save_preferences(
    payload: Preferences, user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> Preferences:
    _require_consent(db, user.id)
    row = db.get(RecommendationPreference, user.id)
    if row is None:
        row = RecommendationPreference(user_id=user.id)
        db.add(row)
    row.settings = payload.model_dump(mode="json")
    db.commit()
    return payload


class Offer(BaseModel):
    cost_minor_per_100g: int = Field(ge=0, le=100000)
    currency: Literal["INR"] = "INR"
    preparation_minutes: int = Field(ge=0, le=240)
    maximum_servings: int = Field(default=2, ge=1, le=10)
    observed_on: date


@router.put("/food-offers/{food_id}")
def offer(
    food_id: UUID, payload: Offer, user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> dict[str, Any]:
    _require_consent(db, user.id)
    if db.get(Food, food_id) is None:
        raise HTTPException(404, "food not found")
    if payload.observed_on > date.today():
        raise HTTPException(422, "price observation cannot be in the future")
    row = db.scalar(
        select(FoodOffer).where(FoodOffer.user_id == user.id, FoodOffer.food_id == food_id)
    )
    if row is None:
        row = FoodOffer(user_id=user.id, food_id=food_id)
        db.add(row)
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return {"food_id": food_id, **payload.model_dump(), "source": "user_entered"}


@router.get("/food-offers")
def offers(user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> list[dict[str, Any]]:
    return [
        {
            "food_id": row.food_id,
            "cost_minor_per_100g": row.cost_minor_per_100g,
            "currency": row.currency,
            "preparation_minutes": row.preparation_minutes,
            "maximum_servings": row.maximum_servings,
            "observed_on": row.observed_on,
            "stale_pricing": (date.today() - row.observed_on).days > 14,
        }
        for row in db.scalars(select(FoodOffer).where(FoodOffer.user_id == user.id))
    ]


@router.get("/recommendations/history")
def history(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> list[dict[str, Any]]:
    _require_consent(db, user.id)
    return [
        {
            "id": row.id,
            "date": row.local_date,
            "candidate_id": row.candidate_id,
            "accepted": row.accepted,
            "score": row.score,
            "model_version": row.model_version,
        }
        for row in db.scalars(
            select(RecommendationDecision)
            .where(RecommendationDecision.user_id == user.id)
            .order_by(RecommendationDecision.created_at.desc())
            .limit(limit)
        )
    ]


@router.get("/recommendations/{decision_id}/explain")
def explain(
    decision_id: UUID,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    format: Literal["compact", "full"] = "full",
) -> dict[str, Any]:
    _require_consent(db, user.id)
    row = db.scalar(
        select(RecommendationDecision).where(
            RecommendationDecision.id == decision_id, RecommendationDecision.user_id == user.id
        )
    )
    if row is None:
        raise HTTPException(404, "decision not found")
    text = row.trace.get(
        "explanation", "Historical decision: inspect the stored calculation trace."
    )
    return {
        "id": row.id,
        "model_version": row.model_version,
        "explanation": text,
        "trace": row.trace if format == "full" else None,
        "llm_used": False,
    }
