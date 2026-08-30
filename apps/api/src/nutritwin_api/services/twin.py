"""On-demand daily/rolling twin calculation from immutable source facts."""

from dataclasses import asdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from nutritwin_domain.coverage import calculate_coverage
from nutritwin_domain.effective import estimate_effective_intake
from nutritwin_domain.intake import IngredientInput, NutrientObservation, aggregate_intake
from nutritwin_domain.risk import RiskInput, score_intake_gap_risk
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from nutritwin_api.models import Food, Meal, MealIngredient, TargetSnapshot


def _dates(end_date: date, days: int) -> list[date]:
    return [end_date - timedelta(days=offset) for offset in reversed(range(days))]


def _load_meals(db: Session, user_id: UUID, start: date, end: date) -> list[Meal]:
    return list(
        db.scalars(
            select(Meal)
            .where(
                Meal.user_id == user_id,
                Meal.local_date >= start,
                Meal.local_date <= end,
                Meal.deleted_at.is_(None),
            )
            .options(
                selectinload(Meal.ingredients)
                .selectinload(MealIngredient.food)
                .selectinload(Food.nutrients)
            )
        ).all()
    )


def _day_aggregate(meals: list[Meal]) -> dict[str, Any]:
    ingredients: list[IngredientInput] = []
    for meal in meals:
        for item in meal.ingredients:
            edible = item.edible_fraction_override or item.food.edible_fraction
            ingredients.append(
                IngredientInput(
                    food_id=str(item.food_id),
                    quantity_g=item.quantity_g,
                    edible_fraction=edible,
                    nutrients=tuple(
                        NutrientObservation(
                            value.nutrient.code,
                            value.amount_per_100g,
                            value.canonical_unit,
                            value.missing_reason,
                        )
                        for value in item.food.nutrients
                    ),
                )
            )
    return aggregate_intake(ingredients) if ingredients else {}


def build_twin_summary(
    db: Session, user_id: UUID, snapshot: TargetSnapshot, end_date: date
) -> dict[str, Any]:
    dates = _dates(end_date, 30)
    meals = _load_meals(db, user_id, dates[0], end_date)
    by_date: dict[date, list[Meal]] = {day: [] for day in dates}
    for meal in meals:
        by_date[meal.local_date].append(meal)
    daily_aggregates = {day: _day_aggregate(day_meals) for day, day_meals in by_date.items()}
    result_nutrients: list[dict[str, Any]] = []
    for target in sorted(snapshot.values, key=lambda item: item.nutrient.code):
        code = target.nutrient.code
        consumed_daily: list[Decimal | None] = []
        complete_daily: list[bool] = []
        effective_daily: list[Decimal | None] = []
        day_traces: list[dict[str, Any]] = []
        for day in dates:
            aggregate = daily_aggregates[day].get(code)
            consumed = aggregate.amount if aggregate is not None else None
            complete = aggregate.complete if aggregate is not None else False
            estimated = estimate_effective_intake(code, consumed, set(), [], day)
            consumed_daily.append(consumed)
            complete_daily.append(complete)
            effective_daily.append(estimated.effective_amount)
            if day == end_date:
                day_traces.append(asdict(estimated))
        daily_consumed = calculate_coverage(consumed_daily[-1:], target.rda)
        rolling_7_consumed = calculate_coverage(consumed_daily[-7:], target.rda)
        rolling_30_consumed = calculate_coverage(consumed_daily, target.rda)
        daily_effective = calculate_coverage(effective_daily[-1:], target.rda)
        rolling_7_effective = calculate_coverage(effective_daily[-7:], target.rda)
        rolling_30_effective = calculate_coverage(effective_daily, target.rda)

        risk: dict[str, Any] | None = None
        if (
            rolling_7_effective.coverage_percent is not None
            and rolling_30_effective.coverage_percent is not None
        ):
            previous_7 = calculate_coverage(effective_daily[-14:-7], target.rda)
            consecutive = 0
            for amount in reversed(effective_daily):
                if amount is None or target.rda is None:
                    break
                daily_percent = amount / target.rda * Decimal("100")
                if daily_percent >= Decimal("80"):
                    break
                consecutive += 1
            known_total = sum(
                (amount for amount in effective_daily if amount is not None), Decimal("0")
            )
            upper_exceeded = bool(
                target.tul is not None and known_total / Decimal("30") > target.tul
            )
            risk_result = score_intake_gap_risk(
                RiskInput(
                    rolling_7_effective.coverage_percent,
                    rolling_30_effective.coverage_percent,
                    consecutive,
                    rolling_7_effective.coverage_percent,
                    previous_7.coverage_percent or rolling_7_effective.coverage_percent,
                    sum(not by_date[day] for day in dates),
                    upper_exceeded,
                )
            )
            risk = asdict(risk_result)
        result_nutrients.append(
            {
                "nutrient_code": code,
                "unit": target.canonical_unit,
                "target": {"rda": target.rda, "ear": target.ear, "tul": target.tul},
                "consumed": {
                    "daily": asdict(daily_consumed),
                    "rolling_7_day": asdict(rolling_7_consumed),
                    "rolling_30_day": asdict(rolling_30_consumed),
                },
                "estimated_effective": {
                    "daily": asdict(daily_effective),
                    "rolling_7_day": asdict(rolling_7_effective),
                    "rolling_30_day": asdict(rolling_30_effective),
                    "calculation_trace": day_traces,
                    "notice": "Estimate only; not measured biological absorption.",
                },
                "risk": risk,
                "composition_complete_today": complete_daily[-1],
            }
        )
    return {
        "as_of_date": end_date,
        "target_snapshot_id": snapshot.id,
        "target_provisional": snapshot.provisional,
        "logged_days_30": sum(bool(by_date[day]) for day in dates),
        "unlogged_days_30": sum(not by_date[day] for day in dates),
        "nutrients": result_nutrients,
        "medical_disclaimer": (
            "NutriTwin is non-diagnostic. Intake-gap indications are not diagnoses, and "
            "estimated effective intake is not measured absorption."
        ),
    }
