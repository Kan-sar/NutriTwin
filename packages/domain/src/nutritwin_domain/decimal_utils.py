"""Decimal helpers shared by scientific calculations."""

from decimal import ROUND_HALF_UP, Decimal

ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")


def decimal(value: Decimal | int | str) -> Decimal:
    """Convert an exact supported input to Decimal without passing through float."""

    if isinstance(value, float):
        raise TypeError("float inputs are not accepted for deterministic nutrition arithmetic")
    return value if isinstance(value, Decimal) else Decimal(value)


def clamp(value: Decimal, minimum: Decimal = ZERO, maximum: Decimal = ONE) -> Decimal:
    if minimum > maximum:
        raise ValueError("minimum cannot exceed maximum")
    return min(maximum, max(minimum, value))


def quantize(value: Decimal, places: str = "0.0001") -> Decimal:
    return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)
