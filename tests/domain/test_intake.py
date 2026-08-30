from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st
from nutritwin_domain.intake import IngredientInput, NutrientObservation, aggregate_intake


def test_consumed_amount_and_missingness_are_both_preserved() -> None:
    ingredients = [
        IngredientInput(
            "known",
            Decimal("50"),
            Decimal("1"),
            (NutrientObservation("iron", Decimal("2"), "mg"),),
        ),
        IngredientInput(
            "unknown",
            Decimal("25"),
            Decimal("1"),
            (NutrientObservation("iron", None, "mg", "not_analysed"),),
        ),
    ]
    result = aggregate_intake(ingredients)["iron"]
    assert result.amount == Decimal("1.0000")
    assert result.complete is False
    assert result.missing_food_ids == ("unknown",)


def test_only_missing_is_not_interpreted_as_zero() -> None:
    result = aggregate_intake(
        [
            IngredientInput(
                "unknown",
                Decimal("100"),
                Decimal("1"),
                (NutrientObservation("iron", None, "mg", "not_reported"),),
            )
        ]
    )["iron"]
    assert result.amount is None


@given(
    quantity=st.decimals(min_value="0.001", max_value="10000", allow_nan=False),
    value=st.decimals(min_value="0", max_value="10000", allow_nan=False),
    edible=st.decimals(min_value="0", max_value="1", allow_nan=False),
)
def test_aggregate_is_never_negative(quantity: Decimal, value: Decimal, edible: Decimal) -> None:
    result = aggregate_intake(
        [
            IngredientInput(
                "food",
                quantity,
                edible,
                (NutrientObservation("iron", value, "mg"),),
            )
        ]
    )["iron"]
    assert result.amount is not None and result.amount >= 0
