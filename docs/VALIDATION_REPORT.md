# Validation report

Updated: 2026-08-31

## Environment and discovery

| Command / check | Observed result |
|---|---|
| Workspace discovery | The original `C:\.cache` directory was unrelated; the project repository is `C:\Projects\NutriTwin` |
| Specification discovery | No separate specification existed before initialization; the approved user brief is preserved in `docs/NUTRITWIN_SPEC.md` |
| `git --version` | `2.52.0.windows.1` |
| `python --version` | `3.14.5` locally; CI targets Python 3.12 |
| `docker --version` | Engine `29.5.2` |
| `docker compose version` | `v5.1.4` |
| Docker Desktop | `4.76`; engine and all project services healthy after the recovery described below |
| `flutter --version` | Unavailable on this host; the Flutter client remains deferred |

## Source and licensing review

The source register records official ICMR-NIN publications, USDA FoodData Central, NIH ODS, ChEBI, FoodOn, RDKit, Playwright, and supporting literature with URLs, access dates, licenses, extraction methods, transformations, and limitations.

- ICMR-NIN RDA/EAR 2020 and IFCT 2017 remain authoritative, but their tables are not bundled because lawful electronic redistribution has not been established.
- Dietary Guidelines for Indians 2024 is used as a governance and educational reference; its electronic-product reuse restrictions are observed.
- The optional USDA FoodData Central `DEMO_KEY` acquisition returned HTTP 429, so no fetched records are included.
- The seven-food/four-nutrient dataset is explicitly synthetic and exists only to validate software behavior.
- ChEBI and FoodOn demo references are provenance-bearing. Qualitative evidence has `calculation_effect=false` and cannot alter intake totals.
- No evidence reviewed for this implementation justifies a universal quantitative absorption multiplier. The active model therefore uses an explicit identity estimate while keeping consumed and estimated-effective fields distinct.

## Final local quality gate

All commands used the repository `.venv` unless noted otherwise.

| Command | Result |
|---|---|
| `ruff check .` | Passed |
| `ruff format --check .` | Passed: 83 files already formatted |
| `python -m mypy apps/api/src packages/domain/src packages/data_pipeline/src services/worker/src scripts` | Passed: no issues in 41 source files |
| `python scripts/validate_data.py` | Passed: 7 foods, 28 nutrient rows, 2 substances, 3 FoodOn mappings, 1 qualitative evidence row; RDKit used |
| `python -m pytest --cov --cov-report=term-missing` | Passed: 40 tests; 83.35% branch-aware coverage; one upstream Starlette deprecation warning |
| `pip-audit` | Passed: no known vulnerabilities; the local project is not a PyPI dependency |
| `detect-secrets-hook --no-verify` over tracked files | Passed; public evidence commit/checksum fields are excluded by exact key regex, and the public Alembic revision identifier is explicitly annotated |
| `docker compose -f infra/docker/compose.yaml config --quiet` | Passed |
| `git diff --check` | Passed before the final commit |
| GitHub Actions CI run `33369863646` for commit `a82ed7a` | Passed: lint, format, typing, RDKit data validation, tests/coverage, migration checks, dependency audit, secret scan, and Compose validation |

## Database, API, and worker validation

Docker Compose was validated with PostgreSQL 16.15, Redis 7.4.10, Neo4j 5.26.30, the FastAPI service, and the Celery worker.

| Check | Result |
|---|---|
| `docker compose ... ps -a` | API, PostgreSQL, Redis, and Neo4j healthy; worker running |
| `GET http://127.0.0.1:8000/health/ready` | `status=ready`, database `postgresql`, PostgreSQL `available`, LLM `disabled` |
| `python scripts/demo.py` | Passed: 4 nutrients, 2 recommendations, `llm_used=false` |
| `docker compose ... exec -T api alembic check` | Passed: no new upgrade operations detected |
| Seeder executed repeatedly in the API container | Passed with stable row counts; no duplicates |
| `celery ... inspect ping` | Passed: one worker returned `pong` |
| Same recomputation job submitted twice | Passed: identical completed result, database `attempts=1` |

The worker emits Celery's expected warning that the development container process runs as root. Production deployment and user remapping remain outside this local prototype.

## Docker Desktop root-cause recovery

Docker Desktop initially crashed before project startup because stale Windows AF_UNIX reparse-point sockets under its local runtime directories could not be removed. Recovery preserved the exact directories instead of deleting Docker data:

- `C:\Users\kanis\AppData\Local\Docker\run.stale-20260830`
- `C:\Users\kanis\AppData\Local\Docker\run.failed-start-20260830`
- `C:\Users\kanis\AppData\Local\docker-secrets-engine.stale-20260830`

The prior settings file was backed up as `C:\Users\kanis\AppData\Roaming\Docker\settings-store.before-nutritwin-inference-fix.20260830.json`; optional local AI/model-runner settings were disabled. Docker recreated clean runtime directories and all NutriTwin containers subsequently started. No factory reset, image/volume purge, or Docker data deletion was performed.

## Validated behavior

- Only Student, Adult, and Admin roles exist; public registration cannot create Admin.
- Argon2 passwords, expiring access JWTs, hashed refresh tokens, rotation, family revocation, and logout are tested.
- Consent gates user workflows; Admin chemistry/reference/audit routes enforce backend RBAC.
- Historical target snapshots remain immutable after profile/reference changes.
- Unit conversion, rounding, float rejection, missingness, and non-negative intake invariants are tested.
- Consumed and estimated-effective intake remain separate throughout domain traces and API responses.
- Daily, rolling 7-day, and rolling 30-day states and persistent intake-gap wording are deterministic and versioned.
- Allergens and dietary restrictions cannot be bypassed by soft objectives.
- Bounded CP-SAT tests cover feasibility, infeasibility, deterministic selection, and serving limits.
- Qualitative interaction evidence cannot modify effective intake.
- Optional LLM, Neo4j enrichment, OCR, barcode, vision, prices, and external integrations can remain disabled without corrupting the core twin.

## Evidence package

Seven screenshots under `docs/review1/evidence/` were captured from the running application and local PostgreSQL state. Browser images retain their original application commit `5f05f39`; the native PowerShell readiness/demo, pytest/coverage, and PostgreSQL images were captured against `baf4fc7`. Manifest schema 2 records the exact timestamp, endpoint or command, application commit, caption, alternative text, and SHA-256 checksum for every image. Images contain demo-only information and exclude passwords, tokens, connection strings, secrets, user identifiers, and personal data.

The consolidated DOCX at `docs/review1/NutriTwin_Project_Review1_Report.docx` contains 67 paragraphs, no tables, 10 inline figures, and one A4 portrait section. It identifies K. Sarthak (`24BDS1121`) as the sole project member. Structural assertions confirmed:

- the requested report term occurs exactly once, in the main heading;
- the only numbered headings are the seven headings supplied in the institutional template, in their original order;
- percentage-milestone wording is absent;
- the academic-use note, evaluation rubric, marks, and assessment-weightage block are absent;
- readiness/demo, automated-test, and PostgreSQL evidence are direct native PowerShell window captures produced by `scripts/capture_powershell_evidence.ps1`, while `scripts/capture_review_evidence.py` preserves those files and captures only browser/API evidence;
- every image has a title and alternative description;
- the accessibility audit reports zero high, medium, or low findings.

LibreOffice rendered all 13 pages to PNG and PDF for visual inspection. Every page was inspected at original render resolution; no overlap, clipping, orphaned heading, rubric content, or blank trailing page was found. Final DOCX SHA-256: `FB86360A970E438364F1ED501A1B83F3F3E78564E7B54E20617C79D9C30FD2B7`.

## Remaining limitations

- Authoritative ICMR-NIN/IFCT rows and scientifically verified golden cases are not enabled.
- Target mappings, the risk heuristic, recommendation objectives, and any future quantitative absorption rules require independent nutrition-expert review.
- Estimated effective intake is a model estimate, not measured biological absorption.
- Materialized scheduled nutrition-memory tables, public CP-SAT construction, pantry, grocery, simulation, full Neo4j graph authoring, research exports, and Flutter are not implemented.
- No participant research, clinical validation, public deployment, or production security assessment has occurred.
- Remote CI will run after the final push; local validation does not claim a remote runner result in advance.
