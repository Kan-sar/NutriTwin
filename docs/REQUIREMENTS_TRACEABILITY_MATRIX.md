# Requirements traceability matrix

Statuses are honest as of repository initialization on 2026-08-30.

| Req | Requirement | Design / data | API or UI | Implementation / test | Status |
|---|---|---|---|---|---|
| R-01 | Roles only Student/Adult/Admin | Access context; User.role | `/auth`, Admin access | planned `nutritwin_api/auth`; RBAC tests | Planned |
| R-02 | Non-diagnostic/non-clinical | Safety vocabulary, explanation assembler | All risk/recommendation surfaces | domain wording tests | Designed |
| R-03 | ICMR-NIN authoritative targets | DataSource/TargetRule/Snapshot | profile target endpoint/Admin sources | local importer + golden tests | Blocked on licensed data |
| R-04 | Consumed vs estimated effective distinct | IntakeTrace/DailySummary columns | meal/twin responses and Flutter labels | effective engine + API tests | Planned |
| R-05 | Daily/7d/30d states | Daily/RollingSummary | twin dashboard endpoints | coverage tests | Planned |
| R-06 | Deterministic transparent versioned risk | RiskSnapshot | risk detail endpoint | risk v1 trace tests | Designed |
| R-07 | Weighted ranking and OR-Tools | Candidate/RecommendationTrace | recommendations endpoint | ranking/CP-SAT tests | Planned |
| R-08 | LLM rephrase only; optional | fact envelope/fallback | explanation response metadata | LLM-disabled/claim-check tests | Designed; adapter deferred |
| R-09 | PostgreSQL transaction/history | relational entities | all core API | migrations/integration tests | Planned |
| R-10 | Neo4j cited relationships, optional | graph adapter/provenance | evidence enrichment | degradation/integration tests | Deferred Phase 8 |
| R-11 | Manual food/ingredient logging core | Food/Meal/Ingredient | food search/meal CRUD | e2e workflow | Planned |
| R-12 | Versioned immutable target trace | TargetRule/Snapshot/Value | target history | immutability/golden tests | Planned |
| R-13 | Evidence-governed absorption | EffectiveRule/IntakeTrace | effective trace | invariant/golden tests | Identity baseline planned; quantitative rules blocked on review |
| R-14 | Edit/delete and idempotent recompute | revisions, task key | meal CRUD/status | Celery retry tests | Planned |
| R-15 | Hard constraints never softened | trace hard checks | recommendation details | allergen/property tests | Planned |
| R-16 | Pantry/grocery/what-if | Phase 7 entities | Phase 7 Flutter/API | optimizer/simulation tests | Deferred |
| R-17 | Admin science/access/audit/export | approval/audit models | Admin surfaces | RBAC/audit/anonymization tests | Partial foundation planned |
| R-18 | Flutter primary client | client architecture | mobile app | widget/e2e tests | Deferred; SDK absent |
| R-19 | Security/privacy controls | threat model and access context | auth/admin/upload boundaries | security tests/scans | Planned |
| R-20 | Reproducible commands/CI/demo | Compose/Makefile/workflow | OpenAPI/demo script | clean-state validation | Planned |

