"""Ingredient-specific, meal/time-scoped resolution of approved evidence."""

from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from nutritwin_domain.effective import EffectiveRule, estimate_effective_intake
from sqlalchemy.orm import Session

from nutritwin_api.models import Meal
from nutritwin_api.services.science import EffectivePayload, eligible_revisions


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def effective_for_meal(
    db: Session, meal: Meal, neighboring: list[Meal], nutrient_code: str
) -> tuple[Decimal | None, list[dict[str, Any]]]:
    records = eligible_revisions(db, meal.local_date)
    values: list[Decimal] = []
    traces: list[dict[str, Any]] = []
    for ingredient in meal.ingredients:
        observations = [n for n in ingredient.food.nutrients if n.nutrient.code == nutrient_code]
        known = [n for n in observations if n.amount_per_100g is not None]
        consumed = None
        if len(known) == 1 and len(observations) == 1:
            edible = (
                ingredient.edible_fraction_override
                if ingredient.edible_fraction_override is not None
                else ingredient.food.edible_fraction
            )
            amount = known[0].amount_per_100g
            assert amount is not None
            consumed = amount * ingredient.quantity_g / 100 * edible
        rules: list[EffectiveRule] = []
        triggers: set[str] = set()
        for record in records:
            p = EffectivePayload.model_validate(record.payload)
            if (
                p.nutrient_code != nutrient_code
                or ingredient.food.food_code not in p.target_food_codes
            ):
                continue
            context = [
                other
                for other in neighboring
                if other.id == meal.id
                or (
                    p.timing_minutes > 0
                    and abs((_utc(other.eaten_at) - _utc(meal.eaten_at)).total_seconds())
                    <= p.timing_minutes * 60
                )
            ]
            present = {item.food.food_code for other in context for item in other.ingredients}
            if p.trigger_food_code not in present:
                continue
            triggers.add(p.trigger_food_code)
            rules.append(
                EffectiveRule(
                    str(record.id),
                    nutrient_code,
                    p.trigger_food_code,
                    p.direction,
                    p.factor,
                    p.minimum_factor,
                    p.maximum_factor,
                    True,
                    p.scientific_review,
                    str(p.citation),
                    p.version,
                    "approved",
                    record.effective_from,
                    record.retired_on,
                    p.priority,
                )
            )
        result = estimate_effective_intake(
            nutrient_code, consumed, triggers, rules, meal.local_date
        )
        if result.effective_amount is not None:
            values.append(result.effective_amount)
        traces.append(
            {"meal_id": str(meal.id), "food_id": str(ingredient.food_id), **asdict(result)}
        )
    return (sum(values, Decimal("0")) if values else None), traces
