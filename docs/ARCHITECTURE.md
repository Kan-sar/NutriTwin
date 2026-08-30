# Architecture

## Decision summary

NutriTwin is a modular monolith with explicit domain boundaries. HTTP, persistence, jobs, and graph adapters call pure deterministic domain functions. PostgreSQL is authoritative; Redis/Celery accelerates recomputation; Neo4j enriches evidence exploration but never owns core nutrition facts.

```text
Flutter (primary, deferred locally) / OpenAPI clients
                         |
                    FastAPI API
  auth | profiles | foods | meals | twin | recommendations | admin
                         |
       application services + transaction boundary
          /              |                  \
 pure domain       PostgreSQL/SQLAlchemy    optional adapters
 target/effective/ history + outbox/audit   Redis/Celery, Neo4j, LLM
 coverage/risk/rank
```

## Modules and current status

| Module | Responsibility | Current status |
|---|---|---|
| `packages/domain` | Units, targets, effective intake, coverage, risk, ranking, optimizer traces | Implemented and tested for the demo slice |
| `packages/data_pipeline` | Source acquisition, normalization and demo-schema validation | Partial: synthetic validator and FDC importer implemented; licensed ICMR/IFCT import blocked |
| `apps/api` | FastAPI routes, application services, configuration, auth/RBAC | Implemented and locally verified |
| PostgreSQL models/migrations | Accounts, profiles, consent, sources, foods, meals, target snapshots, jobs and audit | Implemented for the slice; live PostgreSQL blocked by host Docker failure |
| `services/worker` | Idempotent recomputation | Partial: Celery task and idempotent execution implemented; live broker/scheduling unverified |
| Neo4j adapter | Evidence graph | Stubbed until Phase 8 |
| Flutter | Primary client | Deferred locally; Flutter SDK unavailable |
| Next.js/Kubernetes/vision/barcode/OCR/prices/LLM | Optional scope | Deferred |

## Bounded contexts

- **Access**: users, roles, credentials, refresh sessions, consent, audit.
- **Reference**: sources, nutrients, units, foods, compositions, target schedules, evidence.
- **Twin**: profiles, target snapshots, meals/ingredients, estimates, daily/rolling summaries, risk snapshots.
- **Decision**: candidate meals, constraint results, objective normalization/weights, optimization and explanations.
- **Research/Admin**: review workflows, flags, aggregates, provenance inspection.

Cross-context references use UUIDs and immutable version identifiers. No domain function reads environment variables or performs I/O.

## Persistence and consistency

PostgreSQL transactions atomically write a meal and a recomputation request. The current slice computes summaries on demand for immediate consistency; Celery can repeat the same idempotent operation using `(user_id, affected_date, input_revision, model_version)` uniqueness and stores its result trace on the job. Dedicated materialized summary tables and scheduled dispatch remain deferred. Neo4j population from approved relational evidence records is a Phase 8 design, not current behavior.

## Reliability and graceful degradation

- Liveness never depends on downstream services; readiness reports component state.
- PostgreSQL is required for transactional API operations.
- Redis/Celery failure falls back to synchronous calculation or pending recomputation status.
- Neo4j/LLM/external APIs return unavailable enrichment without changing core results.
- Every optimizer call has bounds, a deterministic seed, and a wall-clock limit.

## Deployment baseline

Docker Compose specifies API, PostgreSQL 16.15, Redis 7.4.10, Neo4j 5.26.30, and a worker with health checks, named development volumes, and loopback-only host ports. Configuration validation passes; live startup is currently unverified because Docker Desktop crashes before the engine becomes available on the validation host. No public exposure or production credentials are included. Kubernetes is intentionally deferred.
