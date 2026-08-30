from datetime import date
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st
from nutritwin_domain.effective import EffectiveRule, estimate_effective_intake


def _rule(rule_id: str, direction: str, factor: str, priority: int = 1) -> EffectiveRule:
    return EffectiveRule(
        id=rule_id,
        target_nutrient="iron",
        trigger_code="demo-trigger",
        direction=direction,  # type: ignore[arg-type]
        factor=Decimal(factor),
        minimum_factor=Decimal("0.5"),
        maximum_factor=Decimal("1.5"),
        quantitative=True,
        evidence_strength="demo-reviewed",
        citation="doi:10.example/demo",
        version="1",
        review_status="approved",
        effective_from=date(2026, 1, 1),
        effective_to=None,
        priority=priority,
    )


def test_identity_baseline_is_separate_and_explicit() -> None:
    result = estimate_effective_intake("iron", Decimal("3.5"), set(), [], date(2026, 8, 30))
    assert result.consumed_amount == result.effective_amount == Decimal("3.5000")
    assert result.applied_rules == ()
    assert "identity_estimate_no_approved_rules" in result.warnings
    assert result.estimation_only is True


def test_rule_is_applied_once_when_duplicate_is_supplied() -> None:
    rule = _rule("r1", "enhance", "1.2")
    result = estimate_effective_intake(
        "iron", Decimal("10"), {"demo-trigger"}, [rule, rule], date(2026, 8, 30)
    )
    assert result.effective_amount == Decimal("12.0000")
    assert len(result.applied_rules) == 1
    assert "duplicate_rule_ignored:r1" in result.warnings


def test_same_priority_conflict_fails_closed() -> None:
    result = estimate_effective_intake(
        "iron",
        Decimal("10"),
        {"demo-trigger"},
        [_rule("enhance", "enhance", "1.2"), _rule("inhibit", "inhibit", "0.8")],
        date(2026, 8, 30),
    )
    assert result.effective_amount == Decimal("10.0000")
    assert result.applied_rules == ()
    assert "conflicting_rules_not_applied:priority_1" in result.warnings


def test_unbounded_factor_is_rejected() -> None:
    with pytest.raises(ValueError):
        _rule("bad", "enhance", "2")


@given(value=st.decimals(min_value="0", max_value="100000", allow_nan=False))
def test_effective_intake_cannot_be_negative(value: Decimal) -> None:
    result = estimate_effective_intake("iron", value, set(), [], date(2026, 8, 30))
    assert result.effective_amount is not None and result.effective_amount >= 0
