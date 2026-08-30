# NutriTwin

NutriTwin is an explainable, non-clinical personalized-nutrition digital-twin academic prototype for Indian dietary contexts. It keeps logged consumed intake, estimated effective intake, reference targets, persistent intake-gap indications, and future simulations as distinct concepts.

> **Safety:** NutriTwin is educational research software. It does not diagnose nutrient deficiency or disease, measure biological absorption, prescribe supplements, or recommend medication changes. Seek a qualified professional for medical or dietary care.

## What works now

The verified backend vertical slice supports Student, Adult, and Admin accounts; consent; versioned profiles and target snapshots; curated food search; ingredient-level meal create/edit/delete; consumed and separately estimated-effective nutrient totals; daily, rolling 7-day, and rolling 30-day coverage; deterministic intake-gap risk traces; hard-constraint-aware weighted meal ranking; and deterministic explanations. The workflow runs with the LLM, Neo4j, OCR, barcode, image recognition, and external prices disabled.

The API foundation also includes Argon2 password hashing, short-lived JWT access tokens, rotating/revocable hashed refresh sessions, backend RBAC, audit events, structured request logging, Alembic migrations, an idempotent Celery recomputation job, Docker Compose, and CI checks.

Authoritative ICMR-NIN tables are **not bundled** because redistribution permission has not been established. The included seven-food/four-nutrient dataset and target rules are conspicuously synthetic and validate software behavior only. They are not nutrition guidance and do not scientifically validate the model.

| Area | Status |
|---|---|
| FastAPI modular monolith and OpenAPI | Implemented and locally verified |
| Pure targets/intake/effective/coverage/risk/ranking/CP-SAT domain logic | Implemented and tested |
| PostgreSQL schema and Alembic migrations | Implemented; migrations also verified against SQLite locally |
| Redis/Celery recomputation | Implemented and unit/integration tested; live container run blocked by host Docker Desktop failure |
| Synthetic demo pipeline and automated HTTP walkthrough | Implemented and verified |
| Licensed ICMR-NIN/IFCT import and scientific golden cases | Blocked on lawful source access/permission |
| Quantitative absorption modifiers | Deferred pending evidence review; identity-estimate baseline implemented |
| Neo4j evidence graph and Admin authoring | Deferred; core is independent of it |
| Flutter, pantry/grocery, what-if, research export | Deferred |
| OCR, vision, barcode, external prices, LLM adapter, Next.js, Kubernetes, deployment | Deferred |

## Architecture

```text
Flutter client (primary; deferred)
                 |
        FastAPI modular monolith
 auth | profiles | foods | meals | twin | recommendations | admin-read
                 |
     pure deterministic domain package
                 |
 PostgreSQL (authoritative history)
      | optional Redis/Celery      optional Neo4j/LLM
```

The complete provisional specification is [docs/NUTRITWIN_SPEC.md](docs/NUTRITWIN_SPEC.md), the architecture is [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), calculation formulas are [docs/ALGORITHM_SPECIFICATION.md](docs/ALGORITHM_SPECIFICATION.md), and requirement status is [docs/REQUIREMENTS_TRACEABILITY_MATRIX.md](docs/REQUIREMENTS_TRACEABILITY_MATRIX.md).

## Quick start with Docker Compose

Prerequisites are Git and a functioning Docker Desktop/Engine. No paid service or external API key is needed.

```bash
make up
make demo
make down
```

The API is at `http://127.0.0.1:8000`; interactive OpenAPI documentation is at `http://127.0.0.1:8000/docs`. Compose publishes only loopback ports. Its credentials are local-development defaults and must be replaced outside local use.

On the validation machine, `docker compose config` passed but Docker Desktop itself crashed while creating its `dockerInference` Unix-socket path. That host-level issue prevented a live Compose run; it is not reported as a successful container test. The local-process workflow below was fully verified.

## Local-process quick start

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock
.venv\Scripts\python.exe -m pip install --no-deps -e .
.venv\Scripts\alembic.exe upgrade head
.venv\Scripts\python.exe scripts\seed.py
.venv\Scripts\uvicorn.exe nutritwin_api.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
.venv\Scripts\python.exe scripts\demo.py
```

The default local database is `nutritwin-dev.db` and is ignored by Git. Set values from `.env.example` to use PostgreSQL or other local services. Unix developers can override `VENV_PYTHON=.venv/bin/python` and `VENV_BIN=.venv/bin` when using the Makefile.

## Developer commands

```bash
make bootstrap
make up
make migrate
make seed
make test
make lint
make typecheck
make validate-data
make demo
make down
```

Exact commands and observed results are recorded in [docs/VALIDATION_REPORT.md](docs/VALIDATION_REPORT.md). The manual/API walkthrough is [docs/DEMO_WALKTHROUGH.md](docs/DEMO_WALKTHROUGH.md).

## Academic review artifact

The consolidated Review-1 report limited to the verified 30% implementation milestone is [docs/review1/NutriTwin_Project_Review1_30_Percent.docx](docs/review1/NutriTwin_Project_Review1_30_Percent.docx). Student name and roll number remain explicit placeholders because those facts were not supplied. The report was structurally audited; visual DOCX-to-PNG rendering could not be performed on the development host because LibreOffice is unavailable.

## Local demo accounts

| Role | Email | Password |
|---|---|---|
| Student | `student@example.com` | `StudentDemo!2026` |
| Adult | `adult@example.com` | `AdultDemo!2026` |
| Admin | `admin@example.com` | `AdminDemo!2026` |

These credentials exist only in seeded local demo data. Do not reuse them or expose this configuration publicly.

## Data provenance

- ICMR-NIN RDA/EAR 2020 remains the required authority for real Indian targets.
- IFCT 2017 is the preferred Indian food-composition source.
- Restricted publications belong in ignored local input directories and require checksum-recorded acquisition/import.
- The optional USDA FoodData Central importer targets CC0 gap/demo records, but the latest unauthenticated acquisition attempt was rate-limited and no FDC records are bundled.
- Missing nutrient values remain missing; an absent value is never silently converted to zero.

See [docs/DATA_SOURCE_REGISTER.md](docs/DATA_SOURCE_REGISTER.md) for source, license, extraction, transformation, and limitation details.

## Repository layout

```text
apps/api/                 FastAPI application and Alembic migrations
apps/mobile/              Flutter implementation contract (deferred)
packages/domain/          Pure deterministic nutrition and optimization logic
packages/data_pipeline/   Reproducible demo/source acquisition validation
services/worker/          Celery task entry point
data/processed/           Legally redistributable generated demo data
infra/docker/             Local reproducible service topology
tests/                    Domain, API, pipeline, migration and job tests
docs/                     Science, architecture, security and validation records
```

## License

No project license has been selected by the user. Until one is added, all rights in repository-authored material remain with the repository owner. Third-party data and citations retain their own terms.
