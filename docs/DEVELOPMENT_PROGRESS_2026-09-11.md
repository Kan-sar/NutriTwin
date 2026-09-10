# NutriTwin development progress — 2026-09-11

## Outcome

Phase 6 advanced from a domain-only CP-SAT prototype to a live, persisted API workflow.
Student and Adult users with active consent and a profile can call
`POST /api/v1/recommendations/construct` to construct a bounded meal from the synthetic
demo catalogue. The response and stored `RecommendationDecision` expose the seed,
constraints, candidate checks, servings, totals, cost, solver status, warnings, and
fallback state. The LLM is not used.

## Implemented behavior

- Uses seven explicitly synthetic foods and project-internal synthetic prices.
- Uses 100 g integer servings with a maximum of two servings per food.
- Enforces the profile dietary pattern before optimization.
- Sets allergenic foods to a zero serving bound and post-validates that no excluded
  allergen was selected.
- Requires positive nutrient minimums in canonical internal units, a bounded budget,
  deterministic seed, and a 50–2,000 ms solver time limit.
- Rejects unknown nutrient codes and excludes candidate foods with unknown requested
  nutrient data rather than interpreting missing composition as zero.
- Persists the complete decision trace using model version `cp-sat-meal-v1`.
- When requested nutrient minimums are infeasible, returns the original infeasible
  status plus a second budget-feasible result that relaxes only nutrient minimums.
  Allergens, dietary restrictions, budget, serving bounds, and time limits remain
  enforced, and unmet amounts are explicit.

## Verification performed

| Check | Observed result |
|---|---|
| Focused optimizer and construction API tests | 7 passed |
| Full `pytest --cov --cov-report=term-missing` | 45 passed; 83.36% branch-aware coverage |
| Ruff lint and format check | Passed; 86 files formatted |
| Strict mypy | Passed; 42 source files |
| RDKit-backed processed-data validation | Passed: 7 foods, 28 nutrient rows, 2 substances, 3 FoodOn mappings, 1 qualitative evidence row |
| Standalone Alembic upgrade and `alembic check` | Upgraded local validation database to `7d8c0f4a2b11`; no new upgrade operations detected |
| Docker Compose rebuild | Passed after Docker Desktop socket recovery |
| Live readiness and construction call | `ready`; optimal spinach/orange result; cost 1850 synthetic minor units; iron 7.2 mg and vitamin C 70 mg |
| PostgreSQL persistence check | `cp-sat-meal-v1` decision row present |
| Live infeasibility call | Explicit `infeasible` status, fallback enabled, warnings and unmet iron returned |

## Docker Desktop recovery

Docker Desktop 4.76 initially failed before the engine started because Windows AF_UNIX
socket reparse points under `Docker\run\dockerInference` and `docker-secrets-engine`
could not be removed. Renaming one directory at a time was insufficient because the
error dialog left Docker backend/frontend processes alive and those processes recreated
the sockets. Recovery stopped only processes whose executables were under
`C:\Program Files\Docker`, preserved both runtime directories using timestamped names,
verified both original paths were absent, and started Docker Desktop once. Engine
29.5.2 and all five NutriTwin services then became healthy. No factory reset, volume
removal, image purge, or project-data deletion occurred.

## Scientific and product limitations

- All construction foods, nutrients, and prices remain synthetic demonstrations.
- The endpoint does not claim nutritional adequacy or provide dietary/medical advice.
- User-supplied minimums are not yet derived automatically from verified ICMR-NIN gap
  targets.
- Preparation time, pantry availability, variety, waste, sustainability, and valid TUL
  constraints are not yet part of this constructor.
- The fallback is a transparent engineering fallback, not a recommendation that unmet
  nutrient requirements are acceptable.
- Production ICMR-NIN/IFCT inputs and quantitative absorption modifiers remain blocked
  on lawful acquisition and scientific review.

## Recommended next work

1. Derive constructor minimums from the stored target/twin gap trace while retaining a
   caller-visible override only for research testing.
2. Add valid TUL constraints and preparation-time metadata with post-validation.
3. Add a retrieval endpoint for historical construction decisions and explanations.
4. Materialize nutrition-memory summaries through Celery with scheduled dispatch and
   PostgreSQL retry tests.
5. Resume Flutter Web bootstrap after the local Flutter tool snapshot is available.
