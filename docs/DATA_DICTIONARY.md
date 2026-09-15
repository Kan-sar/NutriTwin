# Data dictionary

UUID primary keys and UTC timestamps are used unless noted. Scientific numerics are fixed precision decimals. `source_id`, `version`, and `effective_from` are mandatory on reference/rule records.

| Entity | Critical fields | Notes |
|---|---|---|
| User | `id`, `email_normalized`, `password_hash`, `role`, `is_active`, timestamps | Role enum only Student/Adult/Admin; email omitted from research export |
| RefreshSession | `id`, `user_id`, `token_hash`, `family_id`, `expires_at`, `revoked_at`, `replaced_by_id` | Raw refresh token never stored |
| ConsentRecord | `id`, `user_id`, `document_version`, `purpose`, `granted`, `recorded_at` | Append-only events |
| AuditEvent | `id`, `actor_user_id`, `action`, `object_type/id`, `details`, `request_id`, timestamp | No secrets or raw health data |
| Profile | `id`, `user_id`, `birth_date`, `source_sex_category`, `activity_level`, `dietary_pattern`, `allergens`, `revision` (effective dates live in ProfileVersion) | Minimize fields; unsupported physiology absent |
| DataSource | `id`, `code`, `title`, `organization`, `url`, `publication_date`, `license`, `redistribution_status`, `checksum`, `authoritative` | Provenance root |
| Nutrient | `id`, `code`, `name`, `canonical_unit` | Stable codes; e.g. energy/kcal, protein/g, iron/mg |
| TargetRule | `id`, `source_id`, `nutrient_id`, demographic bounds, `ear/rda/tul`, unit, formula key, version/effective dates, review status | Immutable after activation |
| TargetSnapshot | `id`, `user/profile_revision`, `model_version`, `provisional`, `calculated_at`, `trace_json` | Append-only personalized result |
| TargetValue | `snapshot_id`, `nutrient_id`, `ear/rda/tul`, unit, `target_rule_id` | Historical values |
| Food | `id`, `food_code`, `name`, `source_id`, `source_food_id`, `edible_fraction`, `authoritative`, dietary/allergen tags | Food identity separate from composition version |
| FoodNutrient | `food_id`, `nutrient_id`, `amount_per_100g`, unit, `value_status`, `source_version` | Null amount requires missing reason |
| ChemicalSubstance | `id`, preferred name/synonyms, `chebi_id`, formula, canonical SMILES, InChI/InChIKey, `source_id/version`, review/effective dates | Reference identity only; RDKit validates structure consistency |
| FoodOntologyMapping | `food_id`, `source_id`, FoodOn ID/IRI/label, mapping type/confidence, source version, review/effective dates | Exact/broad semantics are explicit; confidence is bounded to 0-1 |
| QualitativeInteractionEvidence | substance, target nutrient, direction, scope/timing, strength, citation, review/version/effective dates, `calculation_effect` | Database check requires `calculation_effect=false`; informational only |
| Meal | `id`, `user_id`, `eaten_at`, `local_date`, `name`, `revision`, `deleted_at` | Ingredient-level log container |
| MealIngredient | `id`, `meal_id`, `food_id`, `quantity_g`, `edible_fraction_override` | Positive bounded quantities |
| EffectiveRule | target nutrient, trigger, timing/scope, factor/formula bounds, evidence strength/citation, version/review/effective dates, priority | Qualitative rules cannot alter totals |
| IntakeTrace | meal/revision, nutrient, consumed/effective, applied rules, intermediate values, warnings, model version | Estimated, never measured absorption |
| DailySummary | user/date/input revision, nutrient, consumed/effective, completeness, model versions | Unique idempotency key |
| RollingSummary | user/end date/window, nutrient, totals/coverage, completeness, input/model versions | Window is 7 or 30 |
| RiskSnapshot | user/date/nutrient, score/band, factor contributions, model version, wording | Non-diagnostic wording |
| RecomputeJob | user, affected date, input revision, model version, status, attempts, result trace, completion timestamp | Unique idempotency tuple; implemented; dedicated summary tables remain deferred |
| CandidateMeal | ID/name, ingredients/servings, cost/time, tags, source | Bounded validated candidate |
| RecommendationTrace | user/date, candidate, hard checks, normalized objectives, weights, score/status/rejections, model version/seed | Explanation source |
| PantryItem | user, food, quantity/unit, expiry, revision | Phase 7 |
| PriceObservation | food, amount/currency/unit, source/manual, observed_at | No fabricated price |
| Simulation | user, scenario/baseline/assumptions/horizon, weekly results, model version/limitations | Projection distinct from twin history |

## Implemented workflow additions

| Entity | Critical fields | Notes |
|---|---|---|
| ProfileVersion | user, revision, effective date, facts JSON | Historical profile context; initial baseline is user-provided |
| ScientificRevision | kind, status, proposer/approver, immutable payload/hash, review record, effective/retired dates | Distinct Admin review; activation is explicit |
| RecommendationPreference | user, settings JSON | Owner-scoped weights and limits |
| FoodOffer | user, food, INR minor units per 100 g, preparation minutes, maximum servings, observation date | Manual price; freshness and ownership checks |
| RecommendationDecision | user/date, candidate, accepted, score, trace, model version | Persisted ranking/construction explanation |

EffectiveRule and candidate results are domain types, not separate ORM tables. IntakeTrace, DailySummary, RollingSummary and RiskSnapshot describe logical results stored within RecomputeJob.result_trace. PantryItem and Simulation are future entities. PriceObservation is currently represented by the bounded owner-scoped FoodOffer model. The ORM and migrations are the executable schema contract.

## Canonical units

Energy `kcal`; mass `g`, `mg`, or `µg` per nutrient registry; ingredient quantity `g`; time `minute`; currency stored as integer minor units plus ISO-4217 code. Unit conversion is explicit at the import/API boundary and never inferred from display labels.
