from decimal import Decimal

from nutritwin_domain.optimizer import FoodOption, construct_meal


def test_optimizer_respects_budget_nutrients_and_serving_bounds() -> None:
    foods = [
        FoodOption("lentil", "Lentil", {"iron": Decimal("3")}, 100, 2),
        FoodOption("spinach", "Spinach", {"iron": Decimal("2")}, 80, 2),
    ]
    result = construct_meal(foods, {"iron": Decimal("5")}, 220, frozenset(), seed=7)
    assert result.status in {"optimal", "feasible"}
    assert result.nutrient_totals["iron"] >= Decimal("5")
    assert result.total_cost_minor <= 220
    assert all(item.servings <= 2 for item in result.servings)


def test_optimizer_never_selects_allergen() -> None:
    result = construct_meal(
        [FoodOption("peanut", "Peanut", {"iron": Decimal("10")}, 10, 2, frozenset({"peanut"}))],
        {"iron": Decimal("1")},
        100,
        frozenset({"peanut"}),
    )
    assert result.status == "infeasible"
    assert result.servings == ()
