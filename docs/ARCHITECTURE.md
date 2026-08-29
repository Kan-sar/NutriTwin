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

| Module | Responsibility | Initial status |
|---|---|---|
| `packages/domain` | Units, targets, effective intake, coverage, risk, ranking, optimizer traces | Planned Phase 1/2 |
| `packages/data_pipeline` | Source manifests, normalization, schema/checksum validation | Planned Phase 2 |
| `apps/api` | FastAPI routes, application services, configuration, auth/RBAC | Planned Phase 1 |
| PostgreSQL models/migrations | Accounts, profiles, consent, sources, foods, meals, snapshots, rules, traces, audit | Planned incrementally |
| `services/worker` | Idempotent recomputation | Partial after vertical slice |
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

PostgreSQL transactions atomically write a meal and a recomputation request. The first slice may recompute synchronously for immediate consistency; Celery repeats the same idempotent operation using `(user_id, affected_date, input_revision, model_version)` uniqueness. Materialized snapshots retain the input revision and complete trace. Neo4j is populated asynchronously from approved relational evidence records.

## Reliability and graceful degradation

- Liveness never depends on downstream services; readiness reports component state.
- PostgreSQL is required for transactional API operations.
- Redis/Celery failure falls back to synchronous calculation or pending recomputation status.
- Neo4j/LLM/external APIs return unavailable enrichment without changing core results.
- Every optimizer call has bounds, a deterministic seed, and a wall-clock limit.

## Deployment baseline

Docker Compose runs API, PostgreSQL 16, Redis 7, Neo4j 5, and an optional worker on a private network with health checks and named development volumes. No public exposure or production credentials are included. Kubernetes is intentionally deferred.

