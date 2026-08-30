"""Transparent deterministic persistent intake-gap risk indication v1."""

from dataclasses import dataclass
from decimal import Decimal

from nutritwin_domain.decimal_utils import HUNDRED, clamp, quantize


@dataclass(frozen=True, slots=True)
class RiskInput:
    coverage_7d_percent: Decimal
    coverage_30d_percent: Decimal
    consecutive_days_below_80: int
    recent_7d_percent: Decimal
    previous_7d_percent: Decimal
    missing_log_days_30d: int
    upper_limit_exceeded: bool


@dataclass(frozen=True, slots=True)
class RiskContribution:
    factor: str
    normalized_value: Decimal
    weight: Decimal
    points: Decimal


@dataclass(frozen=True, slots=True)
class RiskResult:
    score: Decimal
    band: str
    wording: str
    contributions: tuple[RiskContribution, ...]
    model_version: str
    warnings: tuple[str, ...]


def score_intake_gap_risk(
    value: RiskInput, *, model_version: str = "intake-gap-risk-v1"
) -> RiskResult:
    if value.consecutive_days_below_80 < 0 or not 0 <= value.missing_log_days_30d <= 30:
        raise ValueError("duration and missing-day counts must be within bounds")
    threshold = Decimal("80")
    normalized = {
        "gap_7d": clamp((threshold - value.coverage_7d_percent) / threshold),
        "gap_30d": clamp((threshold - value.coverage_30d_percent) / threshold),
        "duration": clamp(Decimal(value.consecutive_days_below_80) / Decimal("30")),
        "declining_trend": Decimal(
            int(value.recent_7d_percent <= value.previous_7d_percent - Decimal("10"))
        ),
        "missing_log_uncertainty": Decimal(value.missing_log_days_30d) / Decimal("30"),
        "upper_limit_exposure": Decimal(int(value.upper_limit_exceeded)),
    }
    weights = {
        "gap_7d": Decimal("0.30"),
        "gap_30d": Decimal("0.35"),
        "duration": Decimal("0.15"),
        "declining_trend": Decimal("0.10"),
        "missing_log_uncertainty": Decimal("0.05"),
        "upper_limit_exposure": Decimal("0.05"),
    }
    contributions = tuple(
        RiskContribution(
            name, normalized[name], weights[name], normalized[name] * weights[name] * HUNDRED
        )
        for name in weights
    )
    score = quantize(sum((item.points for item in contributions), start=Decimal("0")))
    if score < Decimal("25"):
        band = "low"
    elif score < Decimal("50"):
        band = "watch"
    elif score < Decimal("75"):
        band = "elevated"
    else:
        band = "persistent"
    warnings = ("logging_gaps_increase_uncertainty",) if value.missing_log_days_30d else ()
    return RiskResult(
        score=score,
        band=band,
        wording=f"{band} persistent intake-gap risk indication",
        contributions=contributions,
        model_version=model_version,
        warnings=warnings,
    )
