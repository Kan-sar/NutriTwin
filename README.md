# NutriTwin

[![CI](https://github.com/Kan-sar/NutriTwin/actions/workflows/ci.yml/badge.svg)](https://github.com/Kan-sar/NutriTwin/actions/workflows/ci.yml)

An explainable nutrition-journal and digital-twin academic prototype for Indian dietary contexts. Flutter Web connects to a FastAPI backend with deterministic nutrition calculations and PostgreSQL history.

NutriTwin separates consumed intake, estimated effective intake, reference targets, and intake-gap indications. It does not diagnose deficiency, measure absorption, or provide medication or supplement advice.

## Current scope

| Area | Available | Remaining |
|---|---|---|
| Manual journal | Student/Adult accounts, consent, profiles, source-bearing food search, ingredient-level meals | Native mobile packaging and offline sync |
| Nutrition overview | Daily, 7-day and 30-day totals, charts, completeness and calculation traces | Independent scientific validation |
| Meal planning | Demo ranking, constrained construction, editable drafts, saved preferences and private INR prices | Real recipe ranking and authoritative target acceptance |
| Scientific governance | Source/checksum validation, local import, separate Admin review, explicit activation/retirement | Lawful ICMR-NIN inputs and independently reviewed golden cases |
| History and jobs | Profile/target versions, immutable result traces, PostgreSQL outbox, Celery worker and scheduler | Load and concurrency hardening |

The catalogue contains **74 USDA Foundation foods with 12 nutrients**, plus seven synthetic demonstration foods. The USDA subset preserves 751 reported and 137 missing observations. USDA composition is not an Indian target substitute. All bundled targets are explicitly synthetic; no real quantitative absorption factor is enabled by default.

**The strict 70% scientific acceptance gate remains open.** See the [delivery plan](PLANS.md) for phase-level status. Pantry, groceries, what-if simulations, graph editing, research exports and optional recognition features remain deferred.

## Run locally

Use Python 3.12–3.14. From the repository root, with a Python virtual environment activated:

```sh
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
python -m alembic upgrade head
python scripts/seed.py
python -m uvicorn nutritwin_api.main:app --host 127.0.0.1 --port 8000
```

This uses the ignored SQLite development database by default. To run PostgreSQL, Redis, Neo4j, API, worker and scheduler together:

```sh
docker compose -f infra/docker/compose.yaml up --build -d
docker compose -f infra/docker/compose.yaml down
```

Compose binds services to loopback. Its credentials and seeded accounts are local demonstration defaults; do not expose that configuration publicly. `down` preserves named data volumes.

The API documentation is at `http://127.0.0.1:8000/docs`. Run `python scripts/demo.py` in a second activated terminal for the API walkthrough.

For the Flutter client, install **Flutter 3.47.2 / Dart 3.13.2**, then run:

```sh
cd apps/mobile
flutter --no-version-check pub get
flutter --no-version-check run -d chrome --web-hostname 127.0.0.1 --web-port 8080
```

See [client setup](apps/mobile/README.md) for API configuration and the Windows launcher workaround. The [demo walkthrough](docs/DEMO_WALKTHROUGH.md) lists local demo accounts and explains the available flows.

## Verify

```sh
python scripts/check.py
python scripts/check_docs.py
```

These run the backend lint, formatting, type, data and test/coverage checks, plus local documentation-link validation. GNU Make users can run `make check`. For optional chemistry verification, install `requirements-chem.lock` and run `python scripts/validate_data.py --require-rdkit`.

From `apps/mobile`, run `flutter --no-version-check analyze`, `flutter --no-version-check test`, and `flutter --no-version-check build web --release --no-web-resources-cdn`. GitHub Actions checks both Python and Flutter. Historical results and current validation scope are in the [validation report](docs/VALIDATION_REPORT.md).

## Repository guide

```text
apps/api/                 FastAPI application and Alembic migrations
apps/mobile/              Flutter Web client and client tests
packages/domain/          Deterministic calculation and optimization functions
packages/data_pipeline/   Reproducible source transforms and validation
services/worker/          Durable recomputation and scheduled work
infra/docker/             Local service configuration
data/processed/           Redistributable, provenance-bearing fixtures
tests/                    Domain, API, data and integration tests
docs/                     Specification, decisions, source register and validation
```

Start with the [documentation index](docs/README.md), [architecture](docs/ARCHITECTURE.md), [source register](docs/DATA_SOURCE_REGISTER.md), and [scientific import guide](docs/SCIENTIFIC_IMPORT.md). Restricted publications, private inputs, credentials, databases and build outputs are ignored by Git.

The [Review-1 report and evidence](docs/review1/README.md) are retained as dated academic artifacts. They do not describe the latest implementation.

## License

No project license has been selected. Repository-authored material remains under the owner's reserved rights; third-party components and data retain their respective terms in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
