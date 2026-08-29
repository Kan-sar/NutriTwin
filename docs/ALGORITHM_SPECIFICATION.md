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

For each bounded food `i`, integer variable `servings_i ∈ [min_i,max_i]`. Nutrient, cost, and time coefficients are scaled integers with declared scale. Enforce allergens/restrictions by setting upper bound zero, budget/time upper bounds, serving bounds, and valid TUL constraints. Maximize weighted gap coverage minus costs/time/waste with deterministic seed, one search worker, and time limit. Post-validate the result using Decimal domain calculations. If infeasible or timed out, return status and the best validated ranked candidate/fallback; never relax allergens or restrictions.

## Explanation assembler v1

Templates consume only trace fields. Numeric tokens are formatted from those fields and round-tripped in tests. Optional LLM rephrasing receives a structured fact envelope and is rejected if it introduces an unrecognized numeric token or disallowed clinical phrase; deterministic text is the fallback.

