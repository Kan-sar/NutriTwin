# Algorithm specification

All arithmetic uses canonical units and decimal semantics. Inputs, rule/model versions, normalized factors, intermediate values, warnings, and outputs form the persisted calculation trace.

## Target selection v1

Filter active target rows by nutrient, reference source/version, effective date, age interval `[min_age, max_age)`, source-defined sex category when scientifically required, and supported physiological/activity inputs. Select the most specific unique row. If required input or an authorized row is absent, return no target for that nutrient and mark the snapshot provisional; never infer a value.

Snapshot records are append-only. A profile change creates a new target snapshot; it never updates a prior snapshot.

## Intake aggregation v1

For ingredient quantity `q_g` and a food nutrient value `v_per_100g`:

`consumed = q_g / 100 * v_per_100g * edible_fraction`

If `v_per_100g` is missing, the contribution is missing/unknown and is included in completeness metadata, not added as zero. Meal and period totals are sums of known contributions plus a list/count of unknown sources.

## Estimated effective intake v1

Start with `effective = consumed`. Select reviewed, active, in-scope quantitative rules once by unique rule ID. Apply rules in explicit priority order to a declared base using bounded Decimal factors. Clamp only to the documented `[minimum_factor, maximum_factor]`, then require `effective >= 0`. Conflicting same-priority rules fail closed and leave the affected amount unchanged with a warning.

With no eligible quantitative rule, effective equals consumed numerically but remains a separate value and trace containing `identity_estimate_no_approved_rules`. This is an estimate, not measured absorption.

## Nutrition chemistry reference validation v1

ChEBI records are accepted only when their stable identifier, canonical SMILES,
molecular formula, InChI, and InChIKey agree under the pinned RDKit validator. FoodOn
mappings require a stable ID/IRI, explicit exact/close/broad mapping type, confidence in
`[0,1]`, source version, and review status. Duplicate identifiers or conflicting
InChIKeys fail validation.

Qualitative interaction evidence stores direction, meal/timing scope, evidence strength,
citation, review status, version, and effective date. The data validator and database
constraint both require `calculation_effect=false`. No chemistry or qualitative
evidence record participates in the effective-intake rule list.

## Coverage v1

For a target `T > 0` and total `X`, `coverage_percent = 100 * X / T`. Display may be capped separately, but stored coverage is uncapped. Daily uses a local calendar day; rolling 7/30 uses inclusive ending day and the sum of daily amounts divided by `7*T` or `30*T`. Missing target or insufficient composition produces unavailable coverage plus completeness warnings.

## Persistent intake-gap risk v1

This is a deterministic indication, not a deficiency assessment. For each nutrient with valid coverage:

- `gap7 = clamp((80 - coverage7) / 80, 0, 1)`
- `gap30 = clamp((80 - coverage30) / 80, 0, 1)`
- `duration = clamp(consecutive_days_below_80 / 30, 0, 1)`
- `trend = 1` when recent 7-day coverage is at least 10 percentage points below prior 7-day coverage, otherwise `0`
- `adherence = clamp(missing_log_days / 30, 0, 1)` and is reported as uncertainty, not physiological risk
- `upper = 1` only when a valid TUL exists and rolling average exceeds it

`score = 100 * (0.30*gap7 + 0.35*gap30 + 0.15*duration + 0.10*trend + 0.05*adherence + 0.05*upper)`

Bands: `<25 low`, `25–<50 watch`, `50–<75 elevated`, `>=75 persistent`. Each weighted contribution is returned. A later approved model version changes weights/formulas without rewriting v1 traces.

## Weighted candidate ranking v1

First evaluate every hard constraint; any failure rejects the candidate. Normalize each soft objective to `[0,1]`, where 1 is preferred. Missing objective data uses the documented neutral/default policy and adds uncertainty; weights are non-negative and normalized to sum to 1. `score = Σ(weight_i * objective_i)`. Sort by descending score, then stable candidate ID to guarantee deterministic ties.

The first gap-coverage objective is based only on nutrients with valid targets and known composition. Explanations quote stored hard checks, top objective contributions, remaining gaps, provenance, and limitations.

## CP-SAT construction v1

The exposed demo constructor uses only the seven explicitly synthetic foods and synthetic
prices. For each eligible food `i`, integer variable `servings_i ∈ [0,2]`, with one
serving equal to 100 g. Profile dietary tags pre-filter candidates; profile allergens
set the candidate upper bound to zero. Every requested nutrient must have a known value
for a modeled food, so missing composition is never interpreted as zero. Nutrient
coefficients use a declared integer scale; the budget is expressed in synthetic minor
currency units.

The primary model enforces requested nutrient minimums and budget, then maximizes total
requested-nutrient quantity minus cost. It uses a caller-visible deterministic seed, one
search worker, and a bounded 50–2,000 ms time limit. Decimal post-validation verifies
budget, nutrient minimums, and allergens. When the primary model is infeasible or times
out, a second bounded model relaxes only the nutrient minimums and returns the best
budget-feasible selection with `fallback_used=true`, the original status, warnings, and
each unmet amount. Allergen, dietary, budget, serving, and time bounds remain active.
The API persists the full request, candidate checks, solver result, seed, fallback state,
and limitations as a `RecommendationDecision` trace using model `cp-sat-meal-v1`.

## Explanation assembler v1

Templates consume only trace fields. Numeric tokens are formatted from those fields and round-tripped in tests. Optional LLM rephrasing receives a structured fact envelope and is rejected if it introduces an unrecognized numeric token or disallowed clinical phrase; deterministic text is the fallback.
