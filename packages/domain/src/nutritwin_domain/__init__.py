"""Pure deterministic nutrition and decision algorithms for NutriTwin."""

from nutritwin_domain.coverage import CoverageResult, calculate_coverage
from nutritwin_domain.effective import (
    EffectiveIntakeResult,
    EffectiveRule,
    estimate_effective_intake,
)
from nutritwin_domain.intake import IngredientInput, NutrientObservation, aggregate_intake
from nutritwin_domain.risk import RiskInput, RiskResult, score_intake_gap_risk
from nutritwin_domain.targets import ProfileFacts, TargetRule, select_targets

__all__ = [
    "CoverageResult",
    "EffectiveIntakeResult",
    "EffectiveRule",
    "IngredientInput",
    "NutrientObservation",
    "ProfileFacts",
    "RiskInput",
    "RiskResult",
    "TargetRule",
    "aggregate_intake",
    "calculate_coverage",
    "estimate_effective_intake",
    "score_intake_gap_risk",
    "select_targets",
]
