"""Bounded deterministic CP-SAT meal construction."""

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from typing import Literal

from ortools.sat.python import cp_model

OptimizationStatus = Literal["optimal", "feasible", "infeasible", "unknown"]


@dataclass(frozen=True, slots=True)
class FoodOption:
    id: str
    name: str
    nutrient_per_serving: dict[str, Decimal]
    cost_minor_per_serving: int
    maximum_servings: int
    allergens: frozenset[str] = frozenset()
    preparation_minutes: int = 0


@dataclass(frozen=True, slots=True)
class ConstructedServing:
    food_id: str
    servings: int


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    status: OptimizationStatus
    servings: tuple[ConstructedServing, ...]
    total_cost_minor: int
    nutrient_totals: dict[str, Decimal]
    seed: int
    model_version: str
    warnings: tuple[str, ...]


def construct_meal(
    foods: list[FoodOption],
    nutrient_minimums: dict[str, Decimal],
    maximum_budget_minor: int,
    excluded_allergens: frozenset[str],
    *,
    seed: int = 1,
    time_limit_seconds: float = 1.0,
    scale: int = 1000,
    model_version: str = "cp-sat-meal-v2",
    nutrient_maximums: dict[str, Decimal] | None = None,
    maximum_preparation_minutes: int | None = None,
) -> OptimizationResult:
    maximums = nutrient_maximums or {}
    if scale <= 0 or maximum_budget_minor < 0 or time_limit_seconds <= 0:
        raise ValueError("optimizer bounds must be positive")
    if maximum_preparation_minutes is not None and maximum_preparation_minutes < 0:
        raise ValueError("preparation bound cannot be negative")
    if len({food.id for food in foods}) != len(foods):
        raise ValueError("food identifiers must be unique")
    for nutrient, minimum in nutrient_minimums.items():
        if not minimum.is_finite() or minimum < 0:
            raise ValueError(f"nutrient minimum cannot be negative: {nutrient}")
    for food in foods:
        if food.cost_minor_per_serving < 0:
            raise ValueError("food cost cannot be negative")
        if food.preparation_minutes < 0 or food.maximum_servings < 0:
            raise ValueError("food preparation and serving bounds cannot be negative")
        if any(
            not amount.is_finite() or amount < 0 for amount in food.nutrient_per_serving.values()
        ):
            raise ValueError("nutrient amounts cannot be negative")
        missing = (set(nutrient_minimums) | set(maximums)) - set(food.nutrient_per_serving)
        if missing:
            raise ValueError(
                f"missing nutrient data cannot be treated as zero for {food.id}: "
                + ", ".join(sorted(missing))
            )
    model = cp_model.CpModel()
    variables: dict[str, cp_model.IntVar] = {}
    for food in sorted(foods, key=lambda item: item.id):
        upper = 0 if food.allergens & excluded_allergens else food.maximum_servings
        if upper < 0:
            raise ValueError("maximum servings cannot be negative")
        variables[food.id] = model.new_int_var(0, upper, f"servings_{food.id}")
    model.add(
        sum(food.cost_minor_per_serving * variables[food.id] for food in foods)
        <= maximum_budget_minor
    )
    for nutrient, minimum in nutrient_minimums.items():
        model.add(
            sum(
                int(food.nutrient_per_serving.get(nutrient, Decimal("0")) * scale)
                * variables[food.id]
                for food in foods
            )
            >= int((minimum * scale).to_integral_value(rounding=ROUND_CEILING))
        )
    for nutrient, maximum in maximums.items():
        if not maximum.is_finite() or maximum < 0:
            raise ValueError("invalid nutrient maximum")
        model.add(
            sum(
                int(
                    (food.nutrient_per_serving[nutrient] * scale).to_integral_value(
                        rounding=ROUND_CEILING
                    )
                )
                * variables[food.id]
                for food in foods
            )
            <= int((maximum * scale).to_integral_value(rounding=ROUND_FLOOR))
        )
    if maximum_preparation_minutes is not None:
        model.add(
            sum(food.preparation_minutes * variables[food.id] for food in foods)
            <= maximum_preparation_minutes
        )
    total_cost = sum(food.cost_minor_per_serving * variables[food.id] for food in foods)
    # Feasibility first; avoid rewarding a mixture of incomparable nutrient units.
    model.minimize(total_cost * 1000 + sum(variables.values()))

    solver = cp_model.CpSolver()
    solver.parameters.random_seed = seed
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.max_deterministic_time = min(time_limit_seconds, 0.2)
    code = solver.solve(model)
    status_map: dict[cp_model.CpSolverStatus, OptimizationStatus] = {
        cp_model.OPTIMAL: "optimal",
        cp_model.FEASIBLE: "feasible",
        cp_model.INFEASIBLE: "infeasible",
        cp_model.UNKNOWN: "unknown",
        cp_model.MODEL_INVALID: "unknown",
    }
    status = status_map[code]
    if code not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        warning = (
            "requested_constraints_infeasible" if status == "infeasible" else "solve_incomplete"
        )
        return OptimizationResult(status, (), 0, {}, seed, model_version, (warning,))
    selected = tuple(
        ConstructedServing(food.id, solver.value(variables[food.id]))
        for food in sorted(foods, key=lambda item: item.id)
        if solver.value(variables[food.id]) > 0
    )
    totals: dict[str, Decimal] = {}
    food_map = {food.id: food for food in foods}
    cost = 0
    for item in selected:
        food = food_map[item.food_id]
        cost += food.cost_minor_per_serving * item.servings
        for nutrient, amount in food.nutrient_per_serving.items():
            totals[nutrient] = totals.get(nutrient, Decimal("0")) + amount * item.servings
    if cost > maximum_budget_minor:
        raise RuntimeError("post-validation failed: optimizer exceeded budget")
    if any(food_map[item.food_id].allergens & excluded_allergens for item in selected):
        raise RuntimeError("post-validation failed: optimizer selected an excluded allergen")
    if any(
        totals.get(nutrient, Decimal("0")) < minimum
        for nutrient, minimum in nutrient_minimums.items()
    ):
        raise RuntimeError("post-validation failed: optimizer missed nutrient minimum")
    if any(totals.get(n, Decimal("0")) > maximum for n, maximum in maximums.items()):
        raise RuntimeError("post-validation failed: upper limit exceeded")
    if (
        maximum_preparation_minutes is not None
        and sum(food_map[item.food_id].preparation_minutes * item.servings for item in selected)
        > maximum_preparation_minutes
    ):
        raise RuntimeError("post-validation failed: preparation time exceeded")
    return OptimizationResult(status, selected, cost, totals, seed, model_version, ())
