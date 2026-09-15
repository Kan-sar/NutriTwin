"""Persisted, bounded CP-SAT meal construction for the synthetic demo catalogue."""

from dataclasses import asdict
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from nutritwin_domain.optimizer import FoodOption, construct_meal
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from nutritwin_api.models import Food, FoodOffer, Nutrient, Profile, RecommendationDecision

SERVING_GRAMS = Decimal("100")
MAXIMUM_SERVINGS = 2
MODEL_VERSION = "cp-sat-meal-v2"

# Project-internal synthetic prices in Indian paise per 100 g, solely for software tests.
DEMO_COST_MINOR: dict[str, int] = {
    "demo-lentils-cooked": 800,
    "demo-spinach-cooked": 600,
    "demo-tomato-raw": 400,
    "demo-chickpeas-cooked": 900,
    "demo-brown-rice-cooked": 500,
    "demo-yogurt-plain": 700,
    "demo-orange-raw": 650,
}


def construct_demo_meal(
    db: Session,
    user_id: UUID,
    profile: Profile,
    nutrient_minimums: dict[str, Decimal],
    maximum_budget_minor: int,
    as_of_date: date,
    *,
    seed: int,
    time_limit_ms: int,
    demo_mode: bool = True,
    maximum_preparation_minutes: int = 60,
    nutrient_maximums: dict[str, Decimal] | None = None,
) -> dict[str, Any]:
    offers = {
        offer.food_id: offer
        for offer in db.scalars(select(FoodOffer).where(FoodOffer.user_id == user_id))
    }
    foods = list(
        db.scalars(
            select(Food)
            .where(Food.food_code.in_(DEMO_COST_MINOR) if demo_mode else Food.id.in_(offers))
            .options(selectinload(Food.nutrients))
            .order_by(Food.food_code)
        ).all()
    )
    known_nutrients = set(db.scalars(select(Nutrient.code)))
    unknown = set(nutrient_minimums) - known_nutrients
    if unknown:
        raise ValueError("unknown nutrient codes: " + ", ".join(sorted(unknown)))

    required_tags = (
        set() if profile.dietary_pattern == "unrestricted" else {profile.dietary_pattern}
    )
    excluded_allergens = frozenset(profile.allergens)
    options: list[FoodOption] = []
    checks: list[dict[str, Any]] = []
    food_by_id: dict[str, Food] = {}
    for food in foods:
        values = {
            value.nutrient.code: value.amount_per_100g * food.edible_fraction
            for value in food.nutrients
            if value.amount_per_100g is not None
        }
        reasons: list[str] = []
        if required_tags and not required_tags <= set(food.dietary_tags):
            reasons.append("dietary_pattern")
        missing = (set(nutrient_minimums) | set(nutrient_maximums or {})) - set(values)
        if missing:
            reasons.append("unknown_nutrient_data")
        allergen_matches = sorted(set(food.allergens) & excluded_allergens)
        if allergen_matches:
            reasons.append("allergens")
        if not demo_mode and (
            offers[food.id].currency != "INR"
            or offers[food.id].observed_on > as_of_date
            or (as_of_date - offers[food.id].observed_on).days > 14
            or food.food_code.startswith("demo-")
        ):
            reasons.append("unusable_price_or_demo_food")
        eligible_for_model = not set(reasons) & {"dietary_pattern", "unknown_nutrient_data"}
        eligible_for_model = eligible_for_model and "unusable_price_or_demo_food" not in reasons
        checks.append(
            {
                "food_code": food.food_code,
                "eligible_for_model": eligible_for_model,
                "selected": False,
                "rejection_reasons": reasons,
                "allergen_matches": allergen_matches,
            }
        )
        if not eligible_for_model:
            continue
        option = FoodOption(
            id=str(food.id),
            name=food.name,
            nutrient_per_serving={
                code: values[code] for code in set(nutrient_minimums) | set(nutrient_maximums or {})
            },
            cost_minor_per_serving=DEMO_COST_MINOR[food.food_code]
            if demo_mode
            else offers[food.id].cost_minor_per_100g,
            maximum_servings=MAXIMUM_SERVINGS if demo_mode else offers[food.id].maximum_servings,
            allergens=frozenset(food.allergens),
            preparation_minutes=0 if demo_mode else offers[food.id].preparation_minutes,
        )
        options.append(option)
        food_by_id[str(food.id)] = food

    result = construct_meal(
        options,
        nutrient_minimums,
        maximum_budget_minor,
        excluded_allergens,
        seed=seed,
        time_limit_seconds=time_limit_ms / 1000,
        model_version=MODEL_VERSION,
        nutrient_maximums=nutrient_maximums,
        maximum_preparation_minutes=maximum_preparation_minutes,
    )
    selected_by_id = {item.food_id: item.servings for item in result.servings}
    for check in checks:
        food = next(item for item in foods if item.food_code == check["food_code"])
        check["selected"] = str(food.id) in selected_by_id

    servings = [
        {
            "food_id": food.id,
            "food_code": food.food_code,
            "name": food.name,
            "servings": item.servings,
            "grams_per_serving": SERVING_GRAMS,
            "quantity_g": SERVING_GRAMS * item.servings,
            "cost_minor_per_serving": DEMO_COST_MINOR[food.food_code]
            if demo_mode
            else offers[food.id].cost_minor_per_100g,
        }
        for item in result.servings
        for food in (food_by_id[item.food_id],)
    ]
    unmet = {
        code: max(Decimal("0"), minimum - result.nutrient_totals.get(code, Decimal("0")))
        for code, minimum in nutrient_minimums.items()
    }
    trace = {
        "requested_constraints": {
            "nutrient_minimums_canonical_units": nutrient_minimums,
            "maximum_budget_minor": maximum_budget_minor,
            "excluded_allergens": sorted(excluded_allergens),
            "required_dietary_tags": sorted(required_tags),
            "time_limit_ms": time_limit_ms,
            "nutrient_maximums": nutrient_maximums or {},
            "maximum_preparation_minutes": maximum_preparation_minutes,
            "demo_mode": demo_mode,
        },
        "candidate_checks": checks,
        "optimizer": jsonable_encoder(asdict(result), custom_encoder={Decimal: str}),
        "unmet_nutrient_minimums": unmet,
        "fallback_used": "fallback_relaxed_nutrient_minimums" in result.warnings,
    }
    trace["servings"] = servings
    trace["explanation"] = (
        "All hard constraints satisfied; minimized cost and servings."
        if result.status in {"optimal", "feasible"}
        else "No compliant meal found. No hard constraints were relaxed."
    )
    encoded_trace = jsonable_encoder(trace, custom_encoder={Decimal: str})
    decision = RecommendationDecision(
        user_id=user_id,
        local_date=as_of_date,
        candidate_id="cp-sat-constructed-demo-meal" if demo_mode else "cp-sat-constructed-meal",
        accepted=result.status in {"optimal", "feasible"},
        score=None,
        trace=encoded_trace,
        model_version=MODEL_VERSION,
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return {
        "decision_id": decision.id,
        "as_of_date": as_of_date,
        "status": result.status,
        "model_version": MODEL_VERSION,
        "seed": seed,
        "servings": servings,
        "total_cost_minor": result.total_cost_minor,
        "nutrient_totals_canonical_units": result.nutrient_totals,
        "unmet_nutrient_minimums": unmet,
        "fallback_used": trace["fallback_used"],
        "warnings": result.warnings,
        "trace": encoded_trace,
        "notice": (
            "Foods, nutrient values, and prices are synthetic demonstrations. "
            "This deterministic construction is not dietary or medical advice."
        )
        if demo_mode
        else "Source-backed composition and user-entered INR prices; estimation only.",
        "llm_used": False,
    }
