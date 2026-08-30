# NutriTwin delivery plan

Updated: 2026-08-30

## Assumptions and blockers

- The user-provided project brief is captured as the provisional authoritative specification because no separate specification file was available before initialization.
- The repository was created at `C:\Projects\NutriTwin`; the original `C:\.cache` folder was an unrelated cache.
- ICMR-NIN RDA/EAR 2020 and IFCT 2017 tables are not redistributed. A lawful local acquisition/import and expert-verified golden cases are required before real scientific target data can be enabled.
- Python 3.12–3.14 is supported and 3.14.5 was used locally. Flutter is not installed on the development host.
- Docker Compose syntax is verified, but a Docker Desktop host crash involving its `dockerInference` socket blocked live container validation. No factory reset or Docker application-data deletion was performed.
- Pregnancy, lactation, medical conditions, medications, and supplements remain outside the initial target engine. No medical adjustment is inferred.

## Phases and acceptance gates

| Phase | Scope | Validation gate | Status |
|---|---|---|---|
| 0 | Specification, source/open-source register, architecture, algorithms, data model, threat model, ADRs, traceability | Required documents complete and internally consistent | Complete; chemistry/evidence boundary added in ADR 0005 |
| 1 | FastAPI, schema/migrations, auth/RBAC, consent, audit, Redis/Celery entry point, Compose, CI | Health/OpenAPI/auth/RBAC tests; clean migration | Implemented; live Compose blocked by host Docker failure |
| 2 | Profile, target, food search, meal logging, daily/7d/30d twin, risk, ranking, explanation | Automated no-LLM end-to-end API workflow | Complete with synthetic data |
| 2A | Read-only nutrition chemistry foundation | RDKit-validated ChEBI records, reviewed FoodOn mappings, qualitative calculation-inactive evidence and Admin inspection | Implemented for the bounded demo subset; live migration validation pending |
| 3 | Licensed ICMR target import and golden cases | Source checksum and independently verified fixtures | Blocked on lawful data/permission and scientific review |
| 4 | Evidence-governed quantitative absorption rules | Approved evidence records and golden/invariant tests | Partial: safe identity baseline and rule engine invariants implemented; active modifiers deferred |
| 5 | Materialized nutrition memory and scheduled idempotent recomputation | Edit/delete/retry and worker integration tests | Partial: on-demand summaries and idempotent job execution implemented; scheduled materialization deferred |
| 6 | Weighted ranking and bounded deterministic CP-SAT construction | Feasible/infeasible/constraint/trace tests | Partial: ranking is exposed; pure CP-SAT constructor is tested but not yet an API workflow |
| 7 | Pantry, grocery optimization, deterministic what-if | Scenario and invariant tests | Deferred |
| 8 | Evidence graph, Admin workflows, aggregate research export | Graceful degradation, audit and anonymization tests | Partial: Admin read/RBAC and audit foundation only; rest deferred |
| 9 | Flutter client and accessibility/hardening | Unit/widget/end-to-end tests | Deferred; Flutter SDK unavailable |

## Verified vertical-slice criteria

1. Student and Adult accounts can authenticate, consent, create/update a profile, and obtain immutable provisional synthetic targets.
2. A user can search curated foods and create, edit, list, and soft-delete ingredient-level meals.
3. Consumed and estimated-effective totals are separate. With no approved quantitative rule, the trace states that the identity estimate was applied.
4. Daily, rolling 7-day, and rolling 30-day coverage and completeness are deterministic.
5. Risk wording is “persistent intake-gap risk indication” and includes exact factor contributions and model version.
6. Recommendations enforce allergens and dietary restrictions as hard checks, store normalized objectives/weights/rejections, and use deterministic explanations.
7. OR-Tools CP-SAT construction is deterministic and serving-bounded in domain tests.
8. The workflow passes with LLM, Neo4j, OCR, barcode, external price APIs, and vision disabled.
9. Admins can inspect versioned ChEBI/FoodOn/qualitative evidence records, while
   database and pipeline constraints prevent those qualitative rows from changing totals.
10. Review evidence images are captured from a running application, test output, and
    database state with a commit-bound checksum manifest and no secrets.

## Next implementation order

1. Complete live PostgreSQL/Redis/Neo4j migration and evidence capture once Docker
   Desktop or another compatible local engine works.
2. Obtain lawful ICMR-NIN RDA/EAR and IFCT inputs, formalize local import manifests, and
   have reference rows/golden cases independently reviewed.
3. Expose and persist CP-SAT constructed meals with time limits, infeasibility fallback, and decision traces.
4. Add approved absorption evidence authoring/review; keep quantitative rules inactive until the evidence threshold is met.
5. Materialize summary/risk snapshots via Celery and test retry behavior against Redis/PostgreSQL.
6. Implement the Flutter manual workflow before pantry, grocery, graph authoring, or optional recognition integrations.

## Principal risks

| Risk | Mitigation |
|---|---|
| Restricted scientific tables | Local acquisition/import contract, source hashes, synthetic demo data clearly labeled |
| Overstating biological absorption | “Estimated effective intake” naming, identity baseline, uncertainty warning on every trace |
| Clinical interpretation | Constrained wording tests; no disease, medication, supplement, or diagnostic modules |
| Data poisoning or rule tampering | Versioned approvals/citations, Admin RBAC, audit events; full authoring still deferred |
| Optimizer hiding hard violations | Pre-filter and post-validate; record rejection reasons; invariant tests |
| Student-maintained complexity | Modular monolith; optional services degrade safely; web/Kubernetes deferred |
| Research re-identification | Data minimization now; pseudonymization and small-cell suppression before exports |

## Explicitly deferred features

Flutter UI, pantry and grocery workflows, what-if simulation, unrestricted evidence-graph authoring, anonymized research exports, Next.js, Kubernetes, public deployment, OCR, image recognition, barcode scanning, external prices, live LLM rephrasing, condition-specific adjustments, supplement advice, and real participant research.
