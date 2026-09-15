# Algorithm specification

All arithmetic uses canonical units and decimal semantics. Inputs, rule/model versions, normalized factors, intermediate values, warnings, and outputs form the persisted calculation trace.

## Target selection v2

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

## Coverage in twin-summary-v2

For a target `T > 0` and total `X`, `coverage_percent = 100 * X / T`. Display may be capped separately, but stored coverage is uncapped. Daily uses a local calendar day; rolling 7/30 uses the inclusive ending day and divides known amounts by the sum of each day's applicable targets. Missing targets make coverage unavailable. Partial known composition can produce a lower-bound coverage value with `complete=false` and warnings; missing values never become zero.

## Persistent intake-gap risk v1

This is a deterministic indication, not a deficiency assessment. For each nutrient with valid coverage:

- `gap7 = clamp((80 - coverage7) / 80, 0, 1)`
- `gap30 = clamp((80 - coverage30) / 80, 0, 1)`
- `duration = clamp(consecutive_days_below_80 / 30, 0, 1)`
- `trend = 1` when recent 7-day coverage is at least 10 percentage points below prior 7-day coverage, otherwise `0`
- `adherence = clamp(missing_log_days / 30, 0, 1)` and is reported as uncertainty, not physiological risk
- `upper = 1` only when a logged consumed daily amount exceeds that day's applicable TUL

`score = 100 * (0.30*gap7 + 0.35*gap30 + 0.15*duration + 0.10*trend + 0.05*adherence + 0.05*upper)`

Bands: `<25 low`, `25–<50 watch`, `50–<75 elevated`, `>=75 persistent`. Each weighted contribution is returned. A later approved model version changes weights/formulas without rewriting v1 traces.

## Weighted candidate ranking v1

First evaluate every hard constraint; any failure rejects the candidate. Normalize each soft objective to `[0,1]`, where 1 is preferred. Missing objective data uses the documented neutral/default policy and adds uncertainty; weights are non-negative and normalized to sum to 1. `score = Σ(weight_i * objective_i)`. Sort by descending score, then stable candidate ID to guarantee deterministic ties.

The first gap-coverage objective is based only on nutrients with valid targets and known composition. Explanations quote stored hard checks, top objective contributions, remaining gaps, provenance, and limitations.

## CP-SAT construction v2

One integer serving is 100 g. Demo foods have bounded synthetic prices/servings; real candidates require owner-entered INR prices observed within 14 days. Composition is scaled by edible fraction. Relevant missing nutrient data rejects a candidate. Diet and allergens are hard constraints.

The model enforces requested nutrient minima, upper limits, budget, preparation time and serving bounds. Minima use conservative floor coefficients and ceiling right-hand sides; maxima use ceiling coefficients and floor right-hand sides. It minimizes cost times 1,000 plus serving count, with a deterministic seed, one search worker, a deterministic-work limit and a bounded wall-clock limit. Decimal post-validation verifies the requested constraints.

Infeasible or unfinished solves return no compliant meal. Hard constraints are never silently relaxed. The API persists requested constraints, candidate checks, solver result, seed, servings and explanation under `cp-sat-meal-v2`. Real-data construction is gated by authoritative reviewed targets and relevant complete logged composition. Demo mode remains labeled and cannot establish dietary suitability.

## Explanation assembler v1

Templates consume only trace fields. Numeric tokens are formatted from those fields and round-tripped in tests. An LLM adapter is not implemented; configuration rejects enabling it. Any future rephrasing adapter must preserve the trace facts and numerical values.
