"""Ingredient-level consumed nutrient aggregation with explicit missingness."""

from dataclasses import dataclass
from decimal import Decimal

from nutritwin_domain.decimal_utils import HUNDRED, ONE, ZERO, quantize
from nutritwin_domain.units import to_canonical


@dataclass(frozen=True, slots=True)
class NutrientObservation:
    nutrient_code: str
    amount_per_100g: Decimal | None
    unit: str
    missing_reason: str | None = None

    def __post_init__(self) -> None:
        if self.amount_per_100g is None and self.missing_reason is None:
            raise ValueError("missing nutrient amount requires a missing_reason")
        if self.amount_per_100g is not None and self.amount_per_100g < ZERO:
            raise ValueError("nutrient amount cannot be negative")


@dataclass(frozen=True, slots=True)
class IngredientInput:
    food_id: str
    quantity_g: Decimal
    edible_fraction: Decimal
    nutrients: tuple[NutrientObservation, ...]

    def __post_init__(self) -> None:
        if self.quantity_g <= ZERO:
            raise ValueError("ingredient quantity must be positive")
        if not ZERO <= self.edible_fraction <= ONE:
            raise ValueError("edible fraction must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class AggregatedNutrient:
    nutrient_code: str
    amount: Decimal | None
    canonical_unit: str
    complete: bool
    known_contributions: int
    missing_food_ids: tuple[str, ...]


def aggregate_intake(ingredients: list[IngredientInput]) -> dict[str, AggregatedNutrient]:
    nutrient_codes = sorted(
        {observation.nutrient_code for item in ingredients for observation in item.nutrients}
    )
    result: dict[str, AggregatedNutrient] = {}
    for nutrient_code in nutrient_codes:
        amount = ZERO
        known = 0
        missing: list[str] = []
        canonical = ""
        for ingredient in ingredients:
            observations = [
                value for value in ingredient.nutrients if value.nutrient_code == nutrient_code
            ]
            if not observations:
                missing.append(ingredient.food_id)
                continue
            if len(observations) > 1:
                raise ValueError(
                    f"duplicate nutrient {nutrient_code} for food {ingredient.food_id}"
                )
            observation = observations[0]
            if observation.amount_per_100g is None:
                missing.append(ingredient.food_id)
                continue
            converted = to_canonical(nutrient_code, observation.amount_per_100g, observation.unit)
            amount += ingredient.quantity_g / HUNDRED * converted * ingredient.edible_fraction
            known += 1
            canonical = canonical or observation.unit
        from nutritwin_domain.units import canonical_unit

        unit = canonical_unit(nutrient_code)
        result[nutrient_code] = AggregatedNutrient(
            nutrient_code=nutrient_code,
            amount=quantize(amount) if known else None,
            canonical_unit=unit,
            complete=not missing,
            known_contributions=known,
            missing_food_ids=tuple(sorted(set(missing))),
        )
    return result
