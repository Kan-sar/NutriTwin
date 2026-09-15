# Architecture

NutriTwin is a modular monolith. Flutter Web and OpenAPI clients call FastAPI application services, which orchestrate pure deterministic domain functions and PostgreSQL transactions. PostgreSQL owns reference facts, journal records, history and audit. Optional services cannot change the meaning of a calculation.

```text
Flutter Web / OpenAPI
          |
FastAPI: auth | profiles | foods | meals | twin | planning | science review
          |
application services and transaction boundaries
       /                         \
pure domain functions         PostgreSQL / SQLAlchemy
                           history | source versions | audit | durable jobs
                                           |
                                  optional Redis / Celery
                                  worker + beat scheduler
```

## Responsibilities

| Module | Responsibility |
|---|---|
| `apps/mobile` | Manual journal, charts, planning, explanation and Admin review UI; memory-only session tokens |
| `apps/api` | Auth/RBAC, consent, request validation, source/governance workflows and persistence |
| `packages/domain` | Targets, intake, effective-intake rules, coverage, risk, ranking and bounded optimization |
| `packages/data_pipeline` | Reproducible source transforms, missing-value handling, checksums and chemistry validation |
| `services/worker` | Durable queue draining, bounded retry and consent-aware scheduled work |
| `infra/docker` | Loopback-only local PostgreSQL, Redis, Neo4j, API, worker and scheduler |

## History and consistency

A meal mutation and affected-window requests are committed together. Moving a meal invalidates both dates. A computation is identified by `(user_id, affected_date, input_revision, model_version)`. Completed results are preserved; changed dependencies create a new job revision. `RecomputeJob.result_trace` stores daily series, rolling coverage and score contributions; separate duplicate summary tables are not implemented.

Profile versions are effective-dated. Target snapshot keys include profile revision, reference fingerprint and calculation date. Rolling denominators use each day's applicable target. Missing food composition propagates into completeness rather than becoming zero. Initial profile facts are a user-provided historical baseline assumption, as documented in ADR 0006.

Celery beat drains pending work and schedules daily refresh. Failed jobs have bounded retries; a failed row does not starve other jobs. API summary reads can calculate synchronously without Redis. This bounded prototype still needs load and concurrent-failure testing.

## Scientific boundaries

Scientific revisions store immutable payloads and hashes. A separate Admin approves/rejects; activation is explicit. Local source import validates provenance, units and checksums but cannot approve or activate a proposal. Quantitative rules are scoped to ingredients and meal/timing context. ChEBI/FoodOn and qualitative evidence remain calculation-inactive; RDKit runs only in the data pipeline.

Neo4j graph authoring, LLM adapters, OCR, barcode, image recognition and research export remain deferred. Native Flutter packaging and offline synchronization are also outside the current verified scope.

See [ADR 0006](adr/0006-reviewed-science-and-seventy-percent-scope.md), [data dictionary](DATA_DICTIONARY.md), and [validation](VALIDATION_REPORT.md). Docker Desktop recovery and shutdown details belong to the dated validation archive rather than the architecture contract.
