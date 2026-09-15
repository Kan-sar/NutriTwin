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
    daily_amounts: list[Decimal | None],
    target_per_day: Decimal | None,
    *,
    daily_targets: list[Decimal | None] | None = None,
    composition_complete: list[bool] | None = None,
) -> CoverageResult:
    if not daily_amounts:
        raise ValueError("at least one day is required")
    warnings: list[str] = []
    known = [amount for amount in daily_amounts if amount is not None]
    if daily_targets is not None and len(daily_targets) != len(daily_amounts):
        raise ValueError("target and intake windows must have equal length")
    if composition_complete is not None and len(composition_complete) != len(daily_amounts):
        raise ValueError("completeness and intake windows must have equal length")
    targets = daily_targets if daily_targets is not None else [target_per_day] * len(daily_amounts)
    complete = len(known) == len(daily_amounts) and (
        composition_complete is None or all(composition_complete)
    )
    if not complete:
        warnings.append("incomplete_intake_data")
    total = sum(known, start=Decimal("0")) if known else None
    if any(target is None for target in targets):
        warnings.append("target_unavailable")
        coverage = None
    elif any(target is not None and target <= 0 for target in targets):
        raise ValueError("target must be positive")
    elif total is None:
        coverage = None
    else:
        denominator = sum((target for target in targets if target is not None), Decimal("0"))
        coverage = total / denominator * HUNDRED
    return CoverageResult(
        quantize(total) if total is not None else None,
        quantize(target_per_day) if target_per_day is not None else None,
        quantize(coverage) if coverage is not None else None,
        len(daily_amounts),
        complete,
        tuple(warnings),
    )
