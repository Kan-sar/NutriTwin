from decimal import Decimal

from nutritwin_domain.coverage import calculate_coverage
from nutritwin_domain.risk import RiskInput, score_intake_gap_risk


def test_daily_and_rolling_coverage_use_days_times_target() -> None:
    daily = calculate_coverage([Decimal("5")], Decimal("10"))
    rolling = calculate_coverage([Decimal("5")] * 7, Decimal("10"))
    assert daily.coverage_percent == rolling.coverage_percent == Decimal("50.0000")


def test_incomplete_period_is_visible_not_zero_filled() -> None:
    result = calculate_coverage([Decimal("10"), None], Decimal("10"))
    assert result.total_amount == Decimal("10.0000")
    assert result.coverage_percent == Decimal("50.0000")
    assert result.complete is False
    assert "incomplete_intake_data" in result.warnings


def test_risk_trace_sums_exactly_to_score_and_uses_safe_wording() -> None:
    result = score_intake_gap_risk(
        RiskInput(
            coverage_7d_percent=Decimal("40"),
            coverage_30d_percent=Decimal("60"),
            consecutive_days_below_80=15,
            recent_7d_percent=Decimal("40"),
            previous_7d_percent=Decimal("55"),
            missing_log_days_30d=3,
            upper_limit_exceeded=False,
        )
    )
    assert sum((item.points for item in result.contributions), Decimal("0")) == result.score
    assert "intake-gap risk indication" in result.wording
    assert "deficiency" not in result.wording.lower()
