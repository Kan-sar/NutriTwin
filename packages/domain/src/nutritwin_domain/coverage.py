"""Daily and rolling target coverage calculations."""

from dataclasses import dataclass
from decimal import Decimal

from nutritwin_domain.decimal_utils import HUNDRED, quantize


@dataclass(frozen=True, slots=True)
class CoverageResult:
    total_amount: Decimal | None
    target_amount: Decimal | None
    coverage_percent: Decimal | None
    days: int
    complete: bool
    warnings: tuple[str, ...]


def calculate_coverage(
    daily_amounts: list[Decimal | None], target_per_day: Decimal | None
) -> CoverageResult:
    if not daily_amounts:
        raise ValueError("at least one day is required")
    warnings: list[str] = []
    known = [amount for amount in daily_amounts if amount is not None]
    complete = len(known) == len(daily_amounts)
    if not complete:
        warnings.append("incomplete_intake_data")
    total = sum(known, start=Decimal("0")) if known else None
    if target_per_day is None:
        warnings.append("target_unavailable")
        coverage = None
    elif target_per_day <= 0:
        raise ValueError("target must be positive")
    elif total is None:
        coverage = None
    else:
        coverage = total / (target_per_day * len(daily_amounts)) * HUNDRED
    return CoverageResult(
        quantize(total) if total is not None else None,
        quantize(target_per_day) if target_per_day is not None else None,
        quantize(coverage) if coverage is not None else None,
        len(daily_amounts),
        complete,
        tuple(warnings),
    )
