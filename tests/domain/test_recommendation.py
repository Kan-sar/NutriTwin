from decimal import Decimal

from nutritwin_domain.recommendation import (
    CandidateMeal,
    RecommendationContext,
    rank_candidates,
)


def _candidate(candidate_id: str, *, allergens: frozenset[str] = frozenset()) -> CandidateMeal:
    return CandidateMeal(
        id=candidate_id,
        name=candidate_id,
        ingredient_ids=frozenset({candidate_id}),
        allergens=allergens,
        dietary_tags=frozenset({"vegetarian"}),
        cost_minor=500,
        preparation_minutes=10,
        objectives={"gap_coverage": Decimal("0.9"), "cost": Decimal("0.5")},
    )


def test_allergen_is_never_bypassed_by_soft_score() -> None:
    result = rank_candidates(
        [_candidate("unsafe", allergens=frozenset({"peanut"})), _candidate("safe")],
        RecommendationContext(
            excluded_allergens=frozenset({"peanut"}),
            required_dietary_tags=frozenset({"vegetarian"}),
            available_ingredient_ids=None,
            require_available_ingredients=False,
            maximum_budget_minor=1000,
            maximum_preparation_minutes=20,
        ),
        {"gap_coverage": Decimal("0.8"), "cost": Decimal("0.2")},
    )
    assert result[0].candidate_id == "safe"
    unsafe = next(item for item in result if item.candidate_id == "unsafe")
    assert unsafe.accepted is False
    assert unsafe.score is None
    assert unsafe.rejection_reasons == ("allergens",)


def test_tie_break_is_deterministic() -> None:
    context = RecommendationContext(frozenset(), frozenset(), None, False, None, None)
    result = rank_candidates(
        [_candidate("b"), _candidate("a")], context, {"gap_coverage": Decimal("1")}
    )
    assert [item.candidate_id for item in result] == ["a", "b"]
