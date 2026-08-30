"""Deterministic hard-constraint filtering and weighted candidate ranking."""

from dataclasses import dataclass
from decimal import Decimal

from nutritwin_domain.decimal_utils import ONE, ZERO, quantize


@dataclass(frozen=True, slots=True)
class CandidateMeal:
    id: str
    name: str
    ingredient_ids: frozenset[str]
    allergens: frozenset[str]
    dietary_tags: frozenset[str]
    cost_minor: int | None
    preparation_minutes: int
    objectives: dict[str, Decimal]


@dataclass(frozen=True, slots=True)
class RecommendationContext:
    excluded_allergens: frozenset[str]
    required_dietary_tags: frozenset[str]
    available_ingredient_ids: frozenset[str] | None
    require_available_ingredients: bool
    maximum_budget_minor: int | None
    maximum_preparation_minutes: int | None


@dataclass(frozen=True, slots=True)
class RankedCandidate:
    candidate_id: str
    candidate_name: str
    accepted: bool
    hard_constraint_results: dict[str, bool]
    normalized_objectives: dict[str, Decimal]
    normalized_weights: dict[str, Decimal]
    score: Decimal | None
    rejection_reasons: tuple[str, ...]
    explanation: str
    model_version: str


def _normalize_weights(weights: dict[str, Decimal]) -> dict[str, Decimal]:
    if not weights or any(value < ZERO for value in weights.values()):
        raise ValueError("objective weights must be present and non-negative")
    total = sum(weights.values(), start=ZERO)
    if total <= ZERO:
        raise ValueError("at least one objective weight must be positive")
    return {key: value / total for key, value in weights.items()}


def rank_candidates(
    candidates: list[CandidateMeal],
    context: RecommendationContext,
    weights: dict[str, Decimal],
    *,
    model_version: str = "weighted-ranking-v1",
) -> list[RankedCandidate]:
    normalized_weights = _normalize_weights(weights)
    ranked: list[RankedCandidate] = []
    for candidate in candidates:
        checks = {
            "allergens": not bool(candidate.allergens & context.excluded_allergens),
            "dietary_restrictions": context.required_dietary_tags <= candidate.dietary_tags,
            "available_ingredients": (
                not context.require_available_ingredients
                or (
                    context.available_ingredient_ids is not None
                    and candidate.ingredient_ids <= context.available_ingredient_ids
                )
            ),
            "budget": (
                context.maximum_budget_minor is None
                or (
                    candidate.cost_minor is not None
                    and candidate.cost_minor <= context.maximum_budget_minor
                )
            ),
            "preparation_time": (
                context.maximum_preparation_minutes is None
                or candidate.preparation_minutes <= context.maximum_preparation_minutes
            ),
        }
        rejected = tuple(name for name, passed in checks.items() if not passed)
        objective_values: dict[str, Decimal] = {}
        for name in normalized_weights:
            value = candidate.objectives.get(name, Decimal("0.5"))
            if not ZERO <= value <= ONE:
                raise ValueError(f"objective {name} must be normalized to [0,1]")
            objective_values[name] = value
        score = None
        if not rejected:
            score = quantize(
                sum(
                    (
                        normalized_weights[name] * objective_values[name]
                        for name in normalized_weights
                    ),
                    start=ZERO,
                )
            )
            top = max(
                normalized_weights,
                key=lambda name: (normalized_weights[name] * objective_values[name], name),
            )
            explanation = (
                f"{candidate.name} passed all hard constraints and ranked with score "
                f"{score}; its largest weighted contribution was {top}."
            )
        else:
            explanation = (
                f"{candidate.name} was rejected because these hard constraints failed: "
                f"{', '.join(rejected)}."
            )
        ranked.append(
            RankedCandidate(
                candidate.id,
                candidate.name,
                not rejected,
                checks,
                objective_values,
                normalized_weights,
                score,
                rejected,
                explanation,
                model_version,
            )
        )
    return sorted(
        ranked,
        key=lambda item: (
            not item.accepted,
            -(item.score if item.score is not None else ZERO),
            item.candidate_id,
        ),
    )
