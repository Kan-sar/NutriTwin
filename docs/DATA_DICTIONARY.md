# Data dictionary

UUID primary keys and UTC timestamps are used unless noted. Scientific numerics are fixed precision decimals. `source_id`, `version`, and `effective_from` are mandatory on reference/rule records.

| Entity | Critical fields | Notes |
|---|---|---|
| User | `id`, `email_normalized`, `password_hash`, `role`, `is_active`, timestamps | Role enum only Student/Adult/Admin; email omitted from research export |
| RefreshSession | `id`, `user_id`, `token_hash`, `family_id`, `expires_at`, `revoked_at`, `replaced_by_id` | Raw refresh token never stored |
| ConsentRecord | `id`, `user_id`, `document_version`, `purpose`, `granted`, `recorded_at`, `withdrawn_at` | Append-only events |
| AuditEvent | `id`, `actor_user_id`, `action`, `object_type/id`, `before_digest`, `after_digest`, `request_id`, timestamp | No secrets or raw health data |
| Profile | `id`, `user_id`, `birth_date`, `source_sex_category`, `activity_level`, `dietary_pattern`, `allergens`, `effective_from/to`, `revision` | Minimize fields; unsupported physiology absent |
| DataSource | `id`, `code`, `title`, `organization`, `url/doi`, `publication_date`, `license`, `redistribution_status`, `checksum`, `authoritative` | Provenance root |
| Nutrient | `id`, `code`, `name`, `canonical_unit`, `kind` | Stable codes; e.g. energy/kcal, protein/g, iron/mg |
| TargetRule | `id`, `source_id`, `nutrient_id`, demographic bounds, `ear/rda/tul`, unit, formula key, version/effective dates, review status | Immutable after activation |
| TargetSnapshot | `id`, `user/profile_revision`, `model_version`, `provisional`, `calculated_at`, `trace_json` | Append-only personalized result |
| TargetValue | `snapshot_id`, `nutrient_id`, `ear/rda/tul`, unit, `target_rule_id`, `missing_reason` | Historical values |
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

## Canonical units

Energy `kcal`; mass `g`, `mg`, or `µg` per nutrient registry; ingredient quantity `g`; time `minute`; currency stored as integer minor units plus ISO-4217 code. Unit conversion is explicit at the import/API boundary and never inferred from display labels.
