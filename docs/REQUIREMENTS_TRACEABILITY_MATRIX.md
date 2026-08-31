# Requirements traceability matrix

Statuses reflect verified repository behavior on 2026-08-31. “Implemented” requires a passing automated test or command; “partial,” “blocked,” and “deferred” are not completion claims.

| Req | Requirement | Design / data | API or UI | Implementation and evidence | Status |
|---|---|---|---|---|---|
| R-01 | Roles only Student/Adult/Admin | `User.role`, access dependencies | `/auth/*`, `/admin/*` | `models.py`, `security.py`; `tests/api/test_auth.py`, `test_vertical_slice.py` | Implemented |
| R-02 | Non-diagnostic/non-clinical | Safe risk bands and deterministic disclaimer | Twin and recommendation responses | `risk.py`, `services/twin.py`; wording assertions in domain/API tests | Implemented for current surfaces |
| R-03 | ICMR-NIN authoritative targets | `DataSource`, versioned `TargetRule`/snapshot | `/targets/current`, Admin reference read | Synthetic rules are clearly provisional; lawful importer/golden cases unavailable | Blocked on licensed/verified data |
| R-04 | Consumed vs estimated effective distinct | Separate trace/result fields | `/twin/summary` | `effective.py`, `services/twin.py`; effective/API workflow tests | Implemented |
| R-05 | Daily/7d/30d states | Coverage trace with completeness | `/twin/summary` | `coverage.py`; rolling/domain/API tests | Implemented on demand; materialized tables deferred |
| R-06 | Deterministic transparent versioned risk | `intake-gap-risk-v1`, factor contributions | `/twin/summary` | `risk.py`; exact-sum and safe-wording tests | Implemented prototype heuristic |
| R-07 | Weighted ranking and OR-Tools | Candidate trace; CP-SAT result | `/recommendations` exposes ranking | `recommendation.py`, `optimizer.py`; ranking/optimizer tests | Partial: ranking exposed, constructor domain-only |
| R-08 | LLM rephrase only and optional | Deterministic assembler/fallback boundary | Recommendation metadata `llm_used=false` | Deterministic explanations; no LLM adapter; no-LLM API test/demo | Core requirement implemented; adapter deferred |
| R-09 | PostgreSQL transaction/history | SQLAlchemy entities, Alembic revisions | Core API | `models.py`, Alembic; clean migration test/check and live PostgreSQL validation | Implemented |
| R-10 | Neo4j cited relationships, optional | Optional adapter boundary | Future evidence enrichment | Core no-Neo4j workflow tested; graph/edge provenance not built | Deferred Phase 8 |
| R-11 | Manual ingredient logging core | `Food`, `Meal`, `MealIngredient` | food search and meal CRUD | `routers/core.py`; complete API workflow and demo | Implemented |
| R-12 | Versioned immutable target trace | Append-only `TargetSnapshot`/`TargetValue` | `/targets/current` | `services/targets.py`; profile/reference history integration test | Implemented with synthetic references |
| R-13 | Evidence-governed absorption | Pure bounded rule engine and trace | Effective values in twin response | `effective.py`; identity, duplicate, conflict, bound and property tests | Partial: identity baseline active; modifiers blocked on review |
| R-14 | Edit/delete and idempotent recompute | Meal revision; unique `RecomputeJob` tuple | meal PUT/DELETE; worker task | recompute service/task; edit/delete API and repeated-execution tests | Partial: execution implemented, scheduled dispatch unverified |
| R-15 | Hard constraints never softened | Hard checks before normalized scoring | Recommendation accepted/rejected traces | allergen and CP-SAT invariant tests | Implemented for current subset |
| R-16 | Pantry/grocery/what-if | Phase 7 design entities | Future API/Flutter | Data dictionary and plan only | Deferred |
| R-17 | Admin science/access/audit/export | Admin RBAC, audit/source entities | reference/audit read endpoints | `routers/admin.py`; RBAC tests | Partial: inspection foundation only |
| R-18 | Flutter primary client | `/api/v1` client contract | `apps/mobile` | Deferred-status contract only; SDK unavailable | Deferred |
| R-19 | Security/privacy controls | Threat model, minimal profile, tokens, consent, audit | auth/consent/admin boundaries | auth/RBAC tests, Ruff security rules, pip-audit and secret scan | Partial: upload/export controls await those features |
| R-20 | Reproducible commands/CI/demo | Compose, Makefile, pinned lock, CI | OpenAPI and demo script | local checks/demo and live Compose services passed; GitHub Actions run `33369863646` passed for commit `a82ed7a` | Implemented for the current scope |
| R-21 | Basic non-clinical nutrition chemistry | ChEBI substances, FoodOn mappings, qualitative evidence; RDKit validation; calculation-inactive constraint | Admin `/substances` and `/evidence` | chemistry model/migration/fixture/validator; data, API and constraint tests | Implemented for the bounded demo subset |
| R-22 | Working-state screenshots | Commit-bound manifest, captions, alt text, checksums, secret-safe demo records | Swagger/API/test/database evidence images | `scripts/capture_powershell_evidence.ps1` for native terminal windows; `scripts/capture_review_evidence.py` for browser/API captures and manifest; seven images embedded in README and DOCX | Implemented |

## Deferred specification groups

Pantry/grocery, what-if simulation, evidence-graph authoring, full Admin approval workflow, anonymized aggregate export, Flutter, OCR, image recognition, barcode, external prices, optional LLM rephrasing, Next.js, Kubernetes, and public deployment retain their specification requirements but have no implementation claim in the current reviewed scope.
