# Validation report

Updated: 2026-08-30

## Environment and discovery

| Command / check | Observed result |
|---|---|
| `git status --short --branch` in original `C:\.cache` | Not a Git repository; only an unrelated cache was found |
| Searches for `NUTRITWIN_SPEC.md`, `Pasted markdown.md`, and a `# NutriTwin` heading in likely local folders | No separate specification found; the user brief was captured as the provisional specification |
| `git init -b main` in `C:\Projects\NutriTwin` | Passed |
| `git --version` | `2.52.0.windows.1` |
| `python --version` | `3.14.5` |
| `docker --version` | `29.5.2` |
| `docker compose version` | `v5.1.4` |
| `make --version` | Command unavailable; documented Windows commands were used directly |
| `flutter --version` | Command unavailable; Flutter client validation cannot be performed on this host |

## Source and licensing review

Official ICMR-NIN publications/pages, USDA FoodData Central licensing/API documentation, NIH ODS fact sheets, and the PubMed record listed in `DATA_SOURCE_REGISTER.md` were reviewed on 2026-08-30. The findings are:

- Bundled redistribution of the ICMR RDA/EAR tables and IFCT food tables is not currently authorized by the evidence available to this project.
- Dietary Guidelines for Indians 2024 restrict electronic-product reproduction without written permission.
- USDA FoodData Central is CC0, but the scripted `DEMO_KEY` acquisition attempt returned HTTP 429; no FDC data is bundled.
- Available qualitative enhancer/inhibitor evidence does not justify a universal quantitative absorption multiplier. The active baseline therefore leaves estimated effective intake numerically equal to consumed intake while keeping both fields and the uncertainty trace distinct.

## Commands executed and results

All Python commands used the repository `.venv` on Windows unless stated otherwise.

| Command | Result |
|---|---|
| `python -m pip install -r requirements.lock` and `python -m pip install --no-deps -e .` | Passed with pinned dependencies |
| `python scripts/validate_data.py` | Passed: `foods=7`, `nutrient_rows=28`; every record labeled synthetic/non-authoritative |
| `ruff check .` | Passed |
| `ruff format --check .` | Passed: 75 files already formatted |
| `python -m mypy apps/api/src packages/domain/src packages/data_pipeline/src services/worker/src scripts` | Passed: no issues in 39 source files |
| `python -m pytest --cov --cov-report=term-missing` | Passed: 31 tests, total branch-aware coverage 83.22%; one upstream Starlette deprecation warning |
| `alembic upgrade head` against a clean local SQLite database | Passed through both revisions |
| `alembic check` | Passed: no new upgrade operations detected |
| `python scripts/seed.py` twice | Passed twice; seeding is idempotent |
| Local Uvicorn plus `python scripts/demo.py` | Passed: `nutrients=4, recommendations=2, llm_used=false`; demo meal soft-deleted afterward |
| `pip-audit` | Passed: no known vulnerabilities in installed dependencies; local project skipped because it is not a PyPI package |
| `detect-secrets scan --all-files ... --no-verify` with environment/cache exclusions | Passed with zero unallowlisted candidates; public local-only defaults and test/demo fixtures carry explicit allowlist comments |
| `docker compose -f infra/docker/compose.yaml config --quiet` | Passed |
| `docker compose -f infra/docker/compose.yaml up --build -d` | Blocked before build: Docker engine pipe unavailable |
| Local API re-evaluation after final seed | Passed: live/ready 200, OpenAPI title `NutriTwin API` with 17 paths, Student demo passed, Admin read 1 source/4 rules, server stopped and port closed |

## Docker Desktop blocker

Docker Desktop was started in a hidden process for container validation. It crashed during its own inference-manager initialization while attempting to remove/listen on `C:\Users\kanis\AppData\Local\Docker\run\dockerInference`, reporting that the filename, directory name, or volume-label syntax was incorrect. This occurred before NutriTwin images or services started. The Compose topology is syntax-valid, but PostgreSQL/Redis/Neo4j live integration is **not verified** on this host.

No factory reset, recursive deletion, or modification of Docker application data was performed because those actions are destructive and were not necessary to validate the repository configuration.

## Validated behavior

- Only Student, Adult, and Admin roles exist; public registration cannot create Admin.
- Argon2 passwords, expiring access JWTs, hashed refresh tokens, rotation, family revocation, and logout are tested.
- Consent gates the nutrition workflow; Admin reference/audit routes enforce backend RBAC.
- Historical target snapshots remain unchanged when a profile or reference version changes.
- Decimal unit boundaries, rounding, float rejection, missingness, and non-negative intake invariants are tested.
- Consumed and estimated-effective intake are separate in traces and API output.
- The identity-estimate absorption baseline is explicit; duplicate/conflicting/unbounded quantitative rule behavior fails closed in domain tests.
- Daily, 7-day, and 30-day coverage and safe deterministic risk wording are tested.
- Allergens cannot be bypassed by soft objectives; recommendation tie-breaking is deterministic.
- OR-Tools selections respect allergies, budget, nutrient constraints, and serving bounds in domain tests.
- Repeated recomputation execution returns the same completed trace instead of duplicating work.
- The full API demo operates with the LLM and every optional integration disabled.

## Unvalidated or incomplete areas

- Live PostgreSQL, Redis/Celery broker, and Neo4j containers due to the Docker Desktop host failure.
- Flutter code, widget tests, accessibility states, and mobile end-to-end testing.
- Real ICMR-NIN/IFCT imports and authoritative scientific golden cases.
- Active quantitative absorption modifiers and evidence-review workflow.
- Persisted materialized daily/rolling/risk snapshot tables and scheduled Celery execution.
- API-level CP-SAT meal construction, pantry, grocery optimization, what-if simulation, graph authoring, and anonymized research export.
- CI workflow execution on a remote runner; the workflow exists but was not pushed or invoked.

## Scientific limitations and unresolved questions

- Lawful machine-readable access and redistribution terms for required ICMR-NIN/IFCT rows must be resolved.
- Target demographic mappings and every golden example need independent nutrition-expert verification before non-demo use.
- The risk model is a transparent prototype heuristic, not a clinical risk model, and requires external validation.
- No approved quantitative meal-level absorption factor exists in this build; estimated effective intake is not measured absorption.
- Synthetic values only exercise software paths and must never be cited as official recommendations.
