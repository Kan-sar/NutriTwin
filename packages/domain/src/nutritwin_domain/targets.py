"""Versioned personalized target selection without medical inference."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ProfileFacts:
    age_years: Decimal | None
    source_sex_category: str | None
    activity_level: str | None = None


@dataclass(frozen=True, slots=True)
class TargetRule:
    id: str
    nutrient_code: str
    canonical_unit: str
    rda: Decimal | None
    ear: Decimal | None
    tul: Decimal | None
    minimum_age: Decimal
    maximum_age_exclusive: Decimal
    source_sex_category: str | None
    activity_level: str | None
    source_code: str
    source_version: str
    model_version: str
    effective_from: date
    effective_to: date | None
    approved: bool
    authoritative: bool


@dataclass(frozen=True, slots=True)
class TargetTrace:
    nutrient_code: str
    rule_id: str | None
    source_code: str | None
    source_version: str | None
    selection_reason: str
    provisional: bool


@dataclass(frozen=True, slots=True)
class TargetSelection:
    targets: dict[str, TargetRule]
    trace: tuple[TargetTrace, ...]
    provisional: bool
    model_version: str


def _is_effective(rule: TargetRule, on_date: date) -> bool:
    return rule.effective_from <= on_date and (
        rule.effective_to is None or on_date < rule.effective_to
    )


def select_targets(
    profile: ProfileFacts,
    rules: list[TargetRule],
    on_date: date,
    *,
    model_version: str = "target-selection-v1",
) -> TargetSelection:
    """Select at most one target per nutrient and expose every missing/ambiguous case."""

    nutrients = sorted({rule.nutrient_code for rule in rules})
    selected: dict[str, TargetRule] = {}
    trace: list[TargetTrace] = []

    for nutrient in nutrients:
        if profile.age_years is None:
            trace.append(TargetTrace(nutrient, None, None, None, "missing_age", True))
            continue
        candidates = [
            rule
            for rule in rules
            if rule.nutrient_code == nutrient
            and rule.approved
            and _is_effective(rule, on_date)
            and rule.minimum_age <= profile.age_years < rule.maximum_age_exclusive
            and (
                rule.source_sex_category is None
                or rule.source_sex_category == profile.source_sex_category
            )
            and (rule.activity_level is None or rule.activity_level == profile.activity_level)
        ]
        if len(candidates) != 1:
            reason = "no_matching_approved_rule" if not candidates else "ambiguous_target_rules"
            trace.append(TargetTrace(nutrient, None, None, None, reason, True))
            continue
        rule = candidates[0]
        selected[nutrient] = rule
        provisional = not rule.authoritative
        trace.append(
            TargetTrace(
                nutrient,
                rule.id,
                rule.source_code,
                rule.source_version,
                "unique_matching_rule",
                provisional,
            )
        )

    return TargetSelection(
        targets=selected,
        trace=tuple(trace),
        provisional=any(item.provisional for item in trace) or len(selected) != len(nutrients),
        model_version=model_version,
    )
