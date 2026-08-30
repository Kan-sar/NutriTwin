"""Profiles, targets, food search, and ingredient-level meal logging."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from nutritwin_api.database import get_db
from nutritwin_api.models import (
    AuditEvent,
    ConsentRecord,
    Food,
    Meal,
    MealIngredient,
    Profile,
    TargetSnapshot,
)
from nutritwin_api.schemas import (
    FoodNutrientResponse,
    FoodResponse,
    MealCreate,
    MealIngredientRequest,
    MealResponse,
    ProfileResponse,
    ProfileUpsert,
    TargetSnapshotResponse,
    TargetValueResponse,
)
from nutritwin_api.security import CurrentUser
from nutritwin_api.services.recompute import ensure_recompute_job
from nutritwin_api.services.targets import get_or_create_target_snapshot

router = APIRouter(prefix="/api/v1", tags=["core nutrition"])


def _require_consent(db: Session, user_id: uuid.UUID) -> None:
    latest = db.scalar(
        select(ConsentRecord)
        .where(
            ConsentRecord.user_id == user_id,
            ConsentRecord.purpose == "core_application",
        )
        .order_by(ConsentRecord.recorded_at.desc())
        .limit(1)
    )
    if latest is None or not latest.granted:
        raise HTTPException(status_code=409, detail="active core-application consent is required")


def _profile_response(profile: Profile) -> ProfileResponse:
    return ProfileResponse.model_validate(profile)


def _target_response(snapshot: TargetSnapshot) -> TargetSnapshotResponse:
    return TargetSnapshotResponse(
        id=snapshot.id,
        profile_revision=snapshot.profile_revision,
        model_version=snapshot.model_version,
        provisional=snapshot.provisional,
        calculated_at=snapshot.calculated_at,
        trace=snapshot.trace,
        values=[
            TargetValueResponse(
                nutrient_code=value.nutrient.code,
                rda=value.rda,
                ear=value.ear,
                tul=value.tul,
                unit=value.canonical_unit,
                target_rule_id=value.target_rule_id,
            )
            for value in snapshot.values
        ],
    )


@router.put("/profiles/me", response_model=ProfileResponse)
def upsert_profile(
    payload: ProfileUpsert,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ProfileResponse:
    _require_consent(db, user.id)
    if payload.birth_date >= date.today():
        raise HTTPException(status_code=422, detail="birth_date must be in the past")
    profile = db.scalar(select(Profile).where(Profile.user_id == user.id))
    if profile is None:
        profile = Profile(user_id=user.id, **payload.model_dump())
        db.add(profile)
        action = "profile.created"
    else:
        for key, value in payload.model_dump().items():
            setattr(profile, key, value)
        profile.revision += 1
        action = "profile.updated"
    db.flush()
    db.add(
        AuditEvent(
            actor_user_id=user.id, action=action, object_type="profile", object_id=str(profile.id)
        )
    )
    db.commit()
    db.refresh(profile)
    return _profile_response(profile)


@router.get("/profiles/me", response_model=ProfileResponse)
def get_profile(user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> ProfileResponse:
    profile = db.scalar(select(Profile).where(Profile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=404, detail="profile not found")
    return _profile_response(profile)


@router.get("/targets/current", response_model=TargetSnapshotResponse)
def current_targets(
    user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> TargetSnapshotResponse:
    profile = db.scalar(select(Profile).where(Profile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=404, detail="profile not found")
    snapshot = get_or_create_target_snapshot(db, user, profile, date.today())
    return _target_response(snapshot)


def _food_response(food: Food) -> FoodResponse:
    return FoodResponse(
        id=food.id,
        food_code=food.food_code,
        name=food.name,
        source_code=food.source.code,
        source_food_id=food.source_food_id,
        authoritative=food.authoritative,
        dietary_tags=food.dietary_tags,
        allergens=food.allergens,
        nutrients=[
            FoodNutrientResponse(
                nutrient_code=value.nutrient.code,
                amount_per_100g=value.amount_per_100g,
                unit=value.canonical_unit,
                value_status=value.value_status,
                missing_reason=value.missing_reason,
            )
            for value in food.nutrients
        ],
    )


@router.get("/foods", response_model=list[FoodResponse])
def search_foods(
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    query: Annotated[str, Query(min_length=1, max_length=100)],
) -> list[FoodResponse]:
    _require_consent(db, user.id)
    escaped = query.casefold().replace("%", "\\%").replace("_", "\\_")
    foods = db.scalars(
        select(Food)
        .where(func.lower(Food.name).like(f"%{escaped}%", escape="\\"))
        .options(selectinload(Food.source), selectinload(Food.nutrients))
        .order_by(Food.name)
        .limit(25)
    ).all()
    return [_food_response(food) for food in foods]


def _meal_response(meal: Meal) -> MealResponse:
    return MealResponse(
        id=meal.id,
        name=meal.name,
        eaten_at=meal.eaten_at,
        local_date=meal.local_date,
        revision=meal.revision,
        ingredients=[
            MealIngredientRequest(food_id=item.food_id, quantity_g=item.quantity_g)
            for item in meal.ingredients
        ],
    )


def _validated_food_ids(db: Session, ingredients: list[MealIngredientRequest]) -> set[uuid.UUID]:
    requested = {item.food_id for item in ingredients}
    found = set(db.scalars(select(Food.id).where(Food.id.in_(requested))).all())
    if found != requested:
        raise HTTPException(status_code=422, detail="one or more food identifiers are invalid")
    return found


@router.post("/meals", response_model=MealResponse, status_code=status.HTTP_201_CREATED)
def create_meal(
    payload: MealCreate,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> MealResponse:
    _require_consent(db, user.id)
    _validated_food_ids(db, payload.ingredients)
    meal = Meal(
        user_id=user.id,
        name=payload.name,
        eaten_at=payload.eaten_at,
        local_date=payload.local_date,
        ingredients=[
            MealIngredient(food_id=item.food_id, quantity_g=item.quantity_g)
            for item in payload.ingredients
        ],
    )
    db.add(meal)
    db.flush()
    db.add(
        AuditEvent(
            actor_user_id=user.id, action="meal.created", object_type="meal", object_id=str(meal.id)
        )
    )
    ensure_recompute_job(db, user.id, meal.local_date)
    db.commit()
    db.refresh(meal)
    return _meal_response(meal)


@router.get("/meals", response_model=list[MealResponse])
def list_meals(user: CurrentUser, db: Annotated[Session, Depends(get_db)]) -> list[MealResponse]:
    meals = db.scalars(
        select(Meal)
        .where(Meal.user_id == user.id, Meal.deleted_at.is_(None))
        .options(selectinload(Meal.ingredients))
        .order_by(Meal.eaten_at.desc())
    ).all()
    return [_meal_response(meal) for meal in meals]


@router.put("/meals/{meal_id}", response_model=MealResponse)
def update_meal(
    meal_id: uuid.UUID,
    payload: MealCreate,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> MealResponse:
    meal = db.scalar(
        select(Meal)
        .where(Meal.id == meal_id, Meal.user_id == user.id, Meal.deleted_at.is_(None))
        .options(selectinload(Meal.ingredients))
    )
    if meal is None:
        raise HTTPException(status_code=404, detail="meal not found")
    _validated_food_ids(db, payload.ingredients)
    meal.name = payload.name
    meal.eaten_at = payload.eaten_at
    meal.local_date = payload.local_date
    meal.revision += 1
    meal.ingredients = [
        MealIngredient(food_id=item.food_id, quantity_g=item.quantity_g)
        for item in payload.ingredients
    ]
    db.flush()
    ensure_recompute_job(db, user.id, meal.local_date)
    db.commit()
    db.refresh(meal)
    return _meal_response(meal)


@router.delete("/meals/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(
    meal_id: uuid.UUID,
    user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> None:
    meal = db.scalar(
        select(Meal).where(Meal.id == meal_id, Meal.user_id == user.id, Meal.deleted_at.is_(None))
    )
    if meal is None:
        raise HTTPException(status_code=404, detail="meal not found")
    from nutritwin_api.models import utc_now

    meal.deleted_at = utc_now()
    meal.revision += 1
    db.flush()
    ensure_recompute_job(db, user.id, meal.local_date)
    db.commit()
