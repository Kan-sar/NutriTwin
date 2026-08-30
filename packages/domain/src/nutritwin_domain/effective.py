"""Evidence-governed estimated effective intake rule engine."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from nutritwin_domain.decimal_utils import ZERO, quantize

Direction = Literal["enhance", "inhibit"]
ReviewStatus = Literal["draft", "reviewed", "approved", "retired"]


@dataclass(frozen=True, slots=True)
class EffectiveRule:
    id: str
    target_nutrient: str
    trigger_code: str
    direction: Direction
    factor: Decimal | None
    minimum_factor: Decimal
    maximum_factor: Decimal
    quantitative: bool
    evidence_strength: str
    citation: str
    version: str
    review_status: ReviewStatus
    effective_from: date
    effective_to: date | None
    priority: int = 100

    def __post_init__(self) -> None:
        if not self.citation.strip():
            raise ValueError("every effective-intake rule requires a citation")
        if self.minimum_factor < ZERO or self.maximum_factor < self.minimum_factor:
            raise ValueError("invalid factor bounds")
        if self.quantitative and self.factor is None:
            raise ValueError("quantitative rules require a factor")
        if (
            self.factor is not None
            and not self.minimum_factor <= self.factor <= self.maximum_factor
        ):
            raise ValueError("rule factor is outside its declared bounds")


@dataclass(frozen=True, slots=True)
class AppliedRuleTrace:
    rule_id: str
    version: str
    input_amount: Decimal
    factor: Decimal
    output_amount: Decimal
    citation: str


@dataclass(frozen=True, slots=True)
class EffectiveIntakeResult:
    nutrient_code: str
    consumed_amount: Decimal | None
    effective_amount: Decimal | None
    applied_rules: tuple[AppliedRuleTrace, ...]
    evidence_references: tuple[str, ...]
    warnings: tuple[str, ...]
    model_version: str
    estimation_only: bool = True


def _active(rule: EffectiveRule, on_date: date) -> bool:
    return rule.effective_from <= on_date and (
        rule.effective_to is None or on_date < rule.effective_to
    )


def estimate_effective_intake(
    nutrient_code: str,
    consumed_amount: Decimal | None,
    present_triggers: set[str],
    rules: list[EffectiveRule],
    on_date: date,
    *,
    model_version: str = "effective-intake-v1",
) -> EffectiveIntakeResult:
    if consumed_amount is None:
        return EffectiveIntakeResult(
            nutrient_code,
            None,
            None,
            (),
            (),
            ("unknown_consumed_amount", "estimated_not_measured_absorption"),
            model_version,
        )
    if consumed_amount < ZERO:
        raise ValueError("consumed amount cannot be negative")

    eligible: list[EffectiveRule] = []
    seen: set[str] = set()
    warnings: list[str] = []
    evidence: set[str] = set()
    for rule in rules:
        if rule.id in seen:
            warnings.append(f"duplicate_rule_ignored:{rule.id}")
            continue
        seen.add(rule.id)
        if (
            rule.target_nutrient != nutrient_code
            or rule.trigger_code not in present_triggers
            or not _active(rule, on_date)
        ):
            continue
        evidence.add(rule.citation)
        if rule.review_status != "approved" or not rule.quantitative:
            warnings.append(f"context_only_rule:{rule.id}")
            continue
        eligible.append(rule)

    amount = consumed_amount
    applied: list[AppliedRuleTrace] = []
    for priority in sorted({rule.priority for rule in eligible}):
        group = [rule for rule in eligible if rule.priority == priority]
        if {rule.direction for rule in group} == {"enhance", "inhibit"}:
            warnings.append(f"conflicting_rules_not_applied:priority_{priority}")
            continue
        for rule in sorted(group, key=lambda item: item.id):
            assert rule.factor is not None
            output = max(ZERO, amount * rule.factor)
            applied.append(
                AppliedRuleTrace(
                    rule.id,
                    rule.version,
                    quantize(amount),
                    rule.factor,
                    quantize(output),
                    rule.citation,
                )
            )
            amount = output

    if not applied:
        warnings.append("identity_estimate_no_approved_rules")
    warnings.append("estimated_not_measured_absorption")
    return EffectiveIntakeResult(
        nutrient_code=nutrient_code,
        consumed_amount=quantize(consumed_amount),
        effective_amount=quantize(amount),
        applied_rules=tuple(applied),
        evidence_references=tuple(sorted(evidence)),
        warnings=tuple(warnings),
        model_version=model_version,
    )
