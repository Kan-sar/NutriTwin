"""Explicit canonical unit conversion at domain boundaries."""

from decimal import Decimal

from nutritwin_domain.decimal_utils import decimal

CANONICAL_UNITS: dict[str, str] = {
    "energy": "kcal",
    "protein": "g",
    "carbohydrate": "g",
    "fat": "g",
    "fiber": "g",
    "iron": "mg",
    "calcium": "mg",
    "vitamin_c": "mg",
    "vitamin_b12": "ug",
    "folate": "ug",
}

_MASS_TO_GRAMS: dict[str, Decimal] = {
    "g": Decimal("1"),
    "mg": Decimal("0.001"),
    "ug": Decimal("0.000001"),
    "µg": Decimal("0.000001"),
    "mcg": Decimal("0.000001"),
}


def canonical_unit(nutrient_code: str) -> str:
    try:
        return CANONICAL_UNITS[nutrient_code]
    except KeyError as exc:
        raise ValueError(f"unsupported nutrient: {nutrient_code}") from exc


def convert(value: Decimal | int | str, from_unit: str, to_unit: str) -> Decimal:
    """Convert mass units or identity energy units; reject ambiguous conversions."""

    amount = decimal(value)
    source = from_unit.strip().lower()
    target = to_unit.strip().lower()
    if source == target:
        return amount
    if source in _MASS_TO_GRAMS and target in _MASS_TO_GRAMS:
        return amount * _MASS_TO_GRAMS[source] / _MASS_TO_GRAMS[target]
    if source == "kj" and target == "kcal":
        return amount / Decimal("4.184")
    if source == "kcal" and target == "kj":
        return amount * Decimal("4.184")
    raise ValueError(f"unsupported unit conversion: {from_unit} to {to_unit}")


def to_canonical(nutrient_code: str, value: Decimal | int | str, unit: str) -> Decimal:
    return convert(value, unit, canonical_unit(nutrient_code))
