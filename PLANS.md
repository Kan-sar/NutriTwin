# NutriTwin delivery plan

Updated: 2026-08-30

## Assumptions and blockers

- The user-provided project brief is captured as the provisional authoritative specification because no repository attachment was available.
- The repository was intentionally created at `C:\Projects\NutriTwin`; `C:\.cache` was an unrelated cache.
- ICMR-NIN RDA/EAR 2020 and IFCT 2017 full tables are not redistributed. A licensed/local import is required before real scientific target data can be enabled.
- Python 3.12-3.14 is supported. The development host has Python 3.14.5 and Docker; Flutter is not installed.
- Pregnancy, lactation, medical conditions, medications, and supplements are outside the initial personalized target engine. No medical adjustment is inferred.

## Phases and acceptance gates

| Phase | Scope | Dependencies | Validation gate | Status |
|---|---|---|---|---|
| 0 | Specification, source register, architecture, algorithms, data model, threat model, ADRs, traceability | Authoritative-source review | Required documents present and internally consistent | In progress |
| 1 | FastAPI, PostgreSQL, Alembic, auth/RBAC, consent, audit, Redis/Celery, Neo4j health, Compose, CI | Phase 0 | Clean migration; health/auth/RBAC tests | Planned |
| 2 | Profile, versioned target, food search, ingredient meal logging, daily/7d/30d totals, risk, ranked recommendation, explanation | Phase 1; demo data | Automated end-to-end API workflow | Planned |
| 3 | Licensed ICMR target import and golden cases | User-supplied licensed source/permission | Source checksum + verified golden fixtures | Blocked on data permission |
| 4 | Evidence-governed absorption rules | Reviewed quantitative evidence | Golden and invariant tests; no unreviewed active rule | Planned, identity baseline first |
| 5 | Materialized nutrition memory and idempotent Celery recomputation | Phase 2 | Edit/delete/retry tests | Planned |
| 6 | Weighted ranking and bounded deterministic CP-SAT construction | Phase 2, OR-Tools | Feasible/infeasible/constraint/trace tests | Planned |
| 7 | Pantry, grocery optimization, deterministic what-if | Phase 6 | Scenario and invariant tests | Deferred until vertical slice stable |
| 8 | Evidence graph, Admin workflows, aggregate research export | Phase 1-6 | Graceful-degradation and anonymization tests | Deferred |
| 9 | Flutter client and accessibility/hardening | Stable API; Flutter SDK | Unit/widget/e2e tests | Deferred; SDK unavailable locally |

## Initial vertical-slice validation criteria

1. A Student or Adult can register, consent, create a profile, and obtain an immutable demo target marked provisional/synthetic.
2. The user can search curated foods and log ingredient quantities with explicit source and missingness.
3. Consumed and estimated-effective totals are separate outputs; with no approved rules, the trace explicitly reports identity estimation.
4. Daily, 7-day, and 30-day coverage are deterministic and recalculated after edits.
5. Risk wording is always “persistent intake-gap risk indication,” with factor contributions.
6. At least one meal is ranked after hard constraints, and explanation text is assembled only from stored trace facts.
7. The workflow passes with LLM, Neo4j, OCR, barcode, price APIs, and vision disabled.

## Principal risks

| Risk | Mitigation |
|---|---|
| Restricted scientific tables | Local acquisition/import contract; source hashes; synthetic demo data clearly labeled |
| Overstating biological absorption | Rename as estimated effective intake; identity baseline; uncertainty warning on every trace |
| Clinical interpretation | Constrained vocabulary and response tests; no disease/medication/supplement modules |
| Data poisoning or rule tampering | Admin-only versioned approvals, citations, audit events, immutable activated versions |
| Optimizer hiding hard violations | Pre-filter and post-validate candidates; record rejection reasons |
| Student-maintained complexity | Modular monolith; optional services degrade safely; defer Kubernetes and web client |
| Re-identification | Data minimization, pseudonymous exports, small-cell suppression in later research module |

## Explicitly deferred initial features

Flutter UI, Next.js, Kubernetes, public deployment, OCR, image recognition, barcode scanning, external prices, live LLM rephrasing, condition-specific adjustments, supplement advice, real participant research, and unrestricted graph authoring.

