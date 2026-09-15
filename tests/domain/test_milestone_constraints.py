from decimal import Decimal as D

from nutritwin_domain.coverage import calculate_coverage
from nutritwin_domain.optimizer import FoodOption, construct_meal


def test_coverage_uses_each_days_target_and_propagates_partial_composition() -> None:
    result = calculate_coverage(
        [D("5"), D("10")],
        D("10"),
        daily_targets=[D("5"), D("10")],
        composition_complete=[True, False],
    )
    assert result.coverage_percent == D("100")
    assert not result.complete
    missing = calculate_coverage([D("5"), D("10")], D("10"), daily_targets=[None, D("10")])
    assert missing.coverage_percent is None


def test_upper_limit_preparation_and_fractional_minimum_are_never_relaxed() -> None:
    food = FoodOption("food", "Fixture", {"iron": D("1.0001")}, 10, 3, preparation_minutes=10)
    for limits in ({"nutrient_maximums": {"iron": D("1")}}, {"maximum_preparation_minutes": 5}):
        result = construct_meal([food], {"iron": D("1")}, 100, frozenset(), **limits)
        assert result.status == "infeasible" and result.servings == ()
    result = construct_meal([food], {"iron": D("1.0002")}, 100, frozenset())
    assert result.nutrient_totals["iron"] >= D("1.0002")
    assert result.servings[0].servings == 2
