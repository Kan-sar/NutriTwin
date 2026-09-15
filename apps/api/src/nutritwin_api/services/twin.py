"""On-demand daily/rolling twin calculation from immutable source facts."""

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from nutritwin_domain.coverage import calculate_coverage
from nutritwin_domain.intake import IngredientInput, NutrientObservation, aggregate_intake
from nutritwin_domain.risk import RiskInput, score_intake_gap_risk
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from nutritwin_api.models import Food, Meal, MealIngredient, Nutrient, Profile, TargetSnapshot, User
from nutritwin_api.services.effective import effective_for_meal
from nutritwin_api.services.targets import get_or_create_target_snapshot


@dataclass(frozen=True)
class SummaryTarget:
    nutrient: Nutrient
    canonical_unit: str
    rda: Decimal | None
    ear: Decimal | None
    tul: Decimal | None


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
            edible = (
                item.edible_fraction_override
                if item.edible_fraction_override is not None
                else item.food.edible_fraction
            )
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
    neighboring = _load_meals(
        db, user_id, dates[0] - timedelta(days=1), end_date + timedelta(days=1)
    )
    meals = [meal for meal in neighboring if dates[0] <= meal.local_date <= end_date]
    user = db.get(User, user_id)
    profile = db.scalar(select(Profile).where(Profile.user_id == user_id))
    assert user is not None and profile is not None
    historical_targets = {
        day: get_or_create_target_snapshot(db, user, profile, day) for day in dates
    }
    by_date: dict[date, list[Meal]] = {day: [] for day in dates}
    for meal in meals:
        by_date[meal.local_date].append(meal)
    daily_aggregates = {day: _day_aggregate(day_meals) for day, day_meals in by_date.items()}
    result_nutrients: list[dict[str, Any]] = []
    available_targets = {value.nutrient.code: value for value in snapshot.values}
    for nutrient in db.scalars(select(Nutrient).order_by(Nutrient.code)):
        reference_value = available_targets.get(nutrient.code)
        target = SummaryTarget(
            nutrient,
            nutrient.canonical_unit,
            reference_value.rda if reference_value else None,
            reference_value.ear if reference_value else None,
            reference_value.tul if reference_value else None,
        )
        code = target.nutrient.code
        consumed_daily: list[Decimal | None] = []
        complete_daily: list[bool] = []
        effective_daily: list[Decimal | None] = []
        day_traces: list[dict[str, Any]] = []
        target_daily: list[Decimal | None] = []
        for day in dates:
            aggregate = daily_aggregates[day].get(code)
            consumed = aggregate.amount if aggregate is not None else None
            complete = aggregate.complete if aggregate is not None else False
            complete = complete and all(
                sum(
                    n.nutrient.code == code and n.amount_per_100g is not None
                    for n in item.food.nutrients
                )
                == 1
                for meal in by_date[day]
                for item in meal.ingredients
            )
            effective_values: list[Decimal] = []
            for meal in by_date[day]:
                value, traces = effective_for_meal(db, meal, neighboring, code)
                if value is not None:
                    effective_values.append(value)
                if day == end_date:
                    day_traces.extend(traces)
            target_daily.append(
                next(
                    (v.rda for v in historical_targets[day].values if v.nutrient.code == code), None
                )
            )
            consumed_daily.append(consumed)
            complete_daily.append(complete)
            effective_daily.append(
                sum(effective_values, Decimal("0")) if effective_values else None
            )

        def coverage(
            values: list[Decimal | None],
            days: int,
            target_amount: Decimal | None = target.rda,
            targets: list[Decimal | None] = target_daily,
            complete: list[bool] = complete_daily,
        ) -> Any:
            return calculate_coverage(
                values[-days:],
                target_amount,
                daily_targets=targets[-days:],
                composition_complete=complete[-days:],
            )

        daily_consumed = coverage(consumed_daily, 1)
        rolling_7_consumed = coverage(consumed_daily, 7)
        rolling_30_consumed = coverage(consumed_daily, 30)
        daily_effective = coverage(effective_daily, 1)
        rolling_7_effective = coverage(effective_daily, 7)
        rolling_30_effective = coverage(effective_daily, 30)

        risk: dict[str, Any] | None = None
        if (
            rolling_7_effective.coverage_percent is not None
            and rolling_30_effective.coverage_percent is not None
        ):
            previous_7 = calculate_coverage(
                effective_daily[-14:-7],
                target.rda,
                daily_targets=target_daily[-14:-7],
                composition_complete=complete_daily[-14:-7],
            )
            consecutive = 0
            for amount, day_target, complete in reversed(
                list(zip(effective_daily, target_daily, complete_daily, strict=True))
            ):
                if amount is None or day_target is None or not complete:
                    break
                daily_percent = amount / day_target * Decimal("100")
                if daily_percent >= Decimal("80"):
                    break
                consecutive += 1
            upper_exceeded = any(
                amount is not None and limit is not None and amount > limit
                for day, amount in zip(dates, consumed_daily, strict=True)
                for limit in [
                    next(
                        (v.tul for v in historical_targets[day].values if v.nutrient.code == code),
                        None,
                    )
                ]
            )
            risk_result = score_intake_gap_risk(
                RiskInput(
                    rolling_7_effective.coverage_percent,
                    rolling_30_effective.coverage_percent,
                    consecutive,
                    rolling_7_effective.coverage_percent,
                    previous_7.coverage_percent
                    if previous_7.coverage_percent is not None
                    else rolling_7_effective.coverage_percent,
                    sum(not by_date[day] for day in dates),
                    upper_exceeded,
                )
            )
            risk = asdict(risk_result)
            risk["data_complete"] = all(complete_daily)
            if not all(complete_daily):
                risk["warnings"] = [
                    *risk["warnings"],
                    "incomplete_data_not_a_deficiency_assessment",
                ]
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
                "daily_series": [
                    {
                        "date": day,
                        "consumed": consumed_daily[i],
                        "estimated_effective": effective_daily[i],
                        "target": target_daily[i],
                        "complete": complete_daily[i],
                    }
                    for i, day in enumerate(dates)
                ],
            }
        )
    return {
        "as_of_date": end_date,
        "model_version": "twin-summary-v2",
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
