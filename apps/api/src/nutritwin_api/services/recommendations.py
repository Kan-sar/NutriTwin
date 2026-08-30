"""Curated deterministic candidate generation, ranking, and persisted decision traces."""

from dataclasses import asdict
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from nutritwin_domain.intake import IngredientInput, NutrientObservation, aggregate_intake
from nutritwin_domain.recommendation import (
    CandidateMeal,
    RecommendationContext,
    rank_candidates,
)
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from nutritwin_api.models import Food, Profile, RecommendationDecision

TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "id": "demo-lentil-spinach-bowl",
        "name": "DEMO — lentil, spinach, and tomato bowl",
        "ingredients": {
            "demo-lentils-cooked": Decimal("150"),
            "demo-spinach-cooked": Decimal("100"),
            "demo-tomato-raw": Decimal("100"),
        },
        "preparation_minutes": 25,
    },
    {
        "id": "demo-chickpea-rice-bowl",
        "name": "DEMO — chickpea, brown-rice, and tomato bowl",
        "ingredients": {
            "demo-chickpeas-cooked": Decimal("150"),
            "demo-brown-rice-cooked": Decimal("150"),
            "demo-tomato-raw": Decimal("100"),
        },
        "preparation_minutes": 20,
    },
    {
        "id": "demo-yogurt-orange-bowl",
        "name": "DEMO — yogurt and orange bowl",
        "ingredients": {
            "demo-yogurt-plain": Decimal("150"),
            "demo-orange-raw": Decimal("150"),
        },
        "preparation_minutes": 5,
    },
)


def recommend(
    db: Session,
    user_id: UUID,
    profile: Profile,
    target_rdas: dict[str, Decimal],
    as_of_date: date,
) -> list[dict[str, Any]]:
    foods = list(
        db.scalars(
            select(Food).options(selectinload(Food.nutrients), selectinload(Food.source))
        ).all()
    )
    by_code = {food.food_code: food for food in foods}
    candidates: list[CandidateMeal] = []
    for template in TEMPLATES:
        if not set(template["ingredients"]) <= set(by_code):
            continue
        ingredient_inputs: list[IngredientInput] = []
        candidate_foods = [by_code[code] for code in template["ingredients"]]
        for food in candidate_foods:
            ingredient_inputs.append(
                IngredientInput(
                    str(food.id),
                    template["ingredients"][food.food_code],
                    food.edible_fraction,
                    tuple(
                        NutrientObservation(
                            value.nutrient.code,
                            value.amount_per_100g,
                            value.canonical_unit,
                            value.missing_reason,
                        )
                        for value in food.nutrients
                    ),
                )
            )
        totals = aggregate_intake(ingredient_inputs)
        coverage_values: list[Decimal] = []
        for code, target in target_rdas.items():
            total = totals.get(code)
            if total is not None and total.amount is not None and target > 0:
                coverage_values.append(min(Decimal("1"), total.amount / target))
        gap_coverage = (
            sum(coverage_values, Decimal("0")) / len(coverage_values)
            if coverage_values
            else Decimal("0.5")
        )
        dietary_tags = set(candidate_foods[0].dietary_tags)
        for food in candidate_foods[1:]:
            dietary_tags &= set(food.dietary_tags)
        candidates.append(
            CandidateMeal(
                template["id"],
                template["name"],
                frozenset(str(food.id) for food in candidate_foods),
                frozenset(allergen for food in candidate_foods for allergen in food.allergens),
                frozenset(dietary_tags),
                None,
                template["preparation_minutes"],
                {
                    "gap_coverage": gap_coverage,
                    "preparation_time": Decimal("1")
                    - min(Decimal("1"), Decimal(template["preparation_minutes"]) / Decimal("60")),
                    "variety": min(Decimal("1"), Decimal(len(candidate_foods)) / Decimal("3")),
                },
            )
        )
    required_tags = (
        frozenset()
        if profile.dietary_pattern == "unrestricted"
        else frozenset({profile.dietary_pattern})
    )
    ranked = rank_candidates(
        candidates,
        RecommendationContext(
            excluded_allergens=frozenset(profile.allergens),
            required_dietary_tags=required_tags,
            available_ingredient_ids=None,
            require_available_ingredients=False,
            maximum_budget_minor=None,
            maximum_preparation_minutes=45,
        ),
        {
            "gap_coverage": Decimal("0.7"),
            "preparation_time": Decimal("0.2"),
            "variety": Decimal("0.1"),
        },
    )
    output: list[dict[str, Any]] = []
    for item in ranked:
        trace = jsonable_encoder(asdict(item))
        db.add(
            RecommendationDecision(
                user_id=user_id,
                local_date=as_of_date,
                candidate_id=item.candidate_id,
                accepted=item.accepted,
                score=item.score,
                trace=trace,
                model_version=item.model_version,
            )
        )
        output.append(trace)
    db.commit()
    return output
