# NutriTwin implementation checkpoint — 2026-09-14

## Delivered in the working tree

- Flutter Web: Student/Adult registration, sign-in, in-memory rotating tokens, consent and profile, source-bearing food search, editable ingredient journal, daily/7/30-day overview, calculation and risk traces, template ranking, constrained construction, review-before-log drafts, saved preferences, private manual INR prices, decision history, and Admin scientific submissions/review.
- Scientific governance: immutable submissions, two distinct Admin identities, explicit activation/retirement, source and payload hashes, acquisition/review records, bounded ingredient/time-scoped quantitative rules, and a dry-run local import handoff. No real quantitative factors or ICMR values have been invented or activated.
- History: profile versions, date-specific target snapshots, per-day rolling denominators, completeness propagation, explicit zero handling, consumed-intake upper-limit checks, and immutable materialized traces.
- Durable work: PostgreSQL outbox, affected-window recomputation, duplicate-job suppression, bounded retry, consent-aware background processing, Celery worker and scheduler.
- Planning: no hidden hard-constraint relaxation, upper/preparation limits, conservative solver rounding, Decimal post-validation, persisted preference weights, owner-scoped prices and explanation history. Real recipe ranking is still partial; demonstration templates are labeled.
- Data: 74 pinned USDA Foundation foods, 12 nutrient identifiers, 751 reported and 137 missing values, plus the original seven synthetic demonstration foods. USDA is not an Indian target substitute.

## Verified checkpoint

The last complete backend run passed **59 tests with 82.61% coverage**. The final portable full check also passed after all backend changes; see VALIDATION_REPORT.md. Static Python checks pass. Chemistry and dataset validation pass with RDKit.

Flutter's initial and connected client passed three automated tests and static analysis. The release web build succeeded. A live Chrome browser flow passed registration, consent, profile, food search, meal logging, overview, demo ranking, construction, draft creation, and responsive layout. Final chart additions passed analysis, release build, and the repeated browser workflow. Desktop and 390-pixel screenshots were visually inspected.

Docker Desktop was recovered by preserving the stale runtime directory as `run.recovery-20260914-195253`. Containers and volumes were not reset. PostgreSQL, Redis, Neo4j, API, worker, and scheduler started successfully. Live PostgreSQL `alembic check` reported no schema drift, the worker replied to ping, and scheduler/worker logs show durable queue processing.

`make check` could not run because GNU Make is absent. `python scripts/check.py` provides the same required lint, format, type, data, and coverage commands. Current changes are local and uncommitted; no current-head remote CI or production deployment is claimed.

## Gate status

| Gate | Engineering status | Acceptance gap |
|---|---|---|
| 0: architecture and scope | Implemented, ADR 0006 reconciles active choices | Final academic report reconciliation remains separate |
| 1: platform and security | Implemented and locally exercised | Production operations and penetration testing not claimed |
| 2: manual nutrition workflow | Implemented with explicit demonstration targets | Real Indian reference acceptance depends on phase 3 |
| 3: ICMR reference data | Import and review infrastructure implemented | Lawful acquisition and independently reviewed golden fixtures missing |
| 4: quantitative evidence | Governance and scoped runtime implemented | Real reviewed quantitative evidence/golden cases missing |
| 5: materialized memory | Implemented; API and worker checks pass | Load/soak and full concurrent failure campaign remain |
| 6: recommendations | Demo ranking/construction implemented; real-input path gated | Real recipe ranking and scientific real-data acceptance incomplete |
| Flutter manual client | Implemented for Web, brought forward | Android/iOS toolchains and packaging, offline sync, broader accessibility hardening |

**Strict 70% acceptance is not yet met.** Phase count is not a percentage of code written. The remaining scientific gates cannot be satisfied by synthetic tests. Pantry, grocery optimization, what-if simulation, unrestricted graph editing, research exports, clinical features, and optional recognition remain deferred.

## Usage checkpoint

At handoff the five-hour Codex window was 92% used (8% remaining); the weekly window was 30% used (70% remaining). These are account-wide windows, not project completion percentages.
