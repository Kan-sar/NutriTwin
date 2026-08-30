from datetime import date
from decimal import Decimal

from nutritwin_domain.targets import ProfileFacts, TargetRule, select_targets


def _rule(*, authoritative: bool = False) -> TargetRule:
    return TargetRule(
        id="demo-iron-adult",
        nutrient_code="iron",
        canonical_unit="mg",
        rda=Decimal("10"),
        ear=Decimal("8"),
        tul=Decimal("40"),
        minimum_age=Decimal("18"),
        maximum_age_exclusive=Decimal("60"),
        source_sex_category=None,
        activity_level=None,
        source_code="DEMO-SYNTHETIC",
        source_version="1",
        model_version="demo-target-v1",
        effective_from=date(2026, 1, 1),
        effective_to=None,
        approved=True,
        authoritative=authoritative,
    )


def test_unique_demo_rule_is_selected_and_marked_provisional() -> None:
    result = select_targets(ProfileFacts(Decimal("20"), None), [_rule()], date(2026, 8, 30))
    assert result.targets["iron"].rda == Decimal("10")
    assert result.provisional is True
    assert result.trace[0].source_code == "DEMO-SYNTHETIC"


def test_missing_profile_data_never_invents_target() -> None:
    result = select_targets(ProfileFacts(None, None), [_rule()], date(2026, 8, 30))
    assert result.targets == {}
    assert result.trace[0].selection_reason == "missing_age"


def test_ambiguous_rules_fail_closed() -> None:
    result = select_targets(
        ProfileFacts(Decimal("20"), None), [_rule(), _rule()], date(2026, 8, 30)
    )
    assert result.targets == {}
    assert result.trace[0].selection_reason == "ambiguous_target_rules"
