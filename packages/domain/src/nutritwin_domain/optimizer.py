"""Bounded deterministic CP-SAT meal construction."""

from dataclasses import dataclass
from decimal import Decimal
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
    model_version: str = "cp-sat-meal-v1",
) -> OptimizationResult:
    if scale <= 0 or maximum_budget_minor < 0 or time_limit_seconds <= 0:
        raise ValueError("optimizer bounds must be positive")
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
            >= int(minimum * scale)
        )
    total_nutrition = sum(
        sum(int(value * scale) for value in food.nutrient_per_serving.values()) * variables[food.id]
        for food in foods
    )
    total_cost = sum(food.cost_minor_per_serving * variables[food.id] for food in foods)
    model.maximize(total_nutrition * 1000 - total_cost)

    solver = cp_model.CpSolver()
    solver.parameters.random_seed = seed
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = time_limit_seconds
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
        return OptimizationResult(
            status, (), 0, {}, seed, model_version, ("no_valid_constructed_meal",)
        )
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
    if any(
        totals.get(nutrient, Decimal("0")) < minimum
        for nutrient, minimum in nutrient_minimums.items()
    ):
        raise RuntimeError("post-validation failed: optimizer missed nutrient minimum")
    return OptimizationResult(status, selected, cost, totals, seed, model_version, ())
