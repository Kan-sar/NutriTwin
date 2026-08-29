# NutriTwin — An Explainable Personalized Nutrition Digital Twin with Multi-Objective RDA Optimization and Dietary Simulation

Status: provisional authoritative specification captured from the user brief on 2026-08-30. Replace only through an explicit, reviewed specification change.

## Purpose and boundary

NutriTwin is a research-grade academic prototype that helps healthy users understand logged dietary intake relative to versioned Indian nutrient reference targets. It is non-diagnostic, non-clinical, and educational. It must not diagnose disease or nutrient deficiency, prescribe supplements, recommend medication changes, or claim that a computed estimate equals biological absorption.

## Roles

Only Student, Adult, and Admin roles exist. Student and Adult are application personas with equivalent safety boundaries; age eligibility is represented in the profile and never inferred from role. Admin manages access, reference versions, evidence, rules, feature flags, and audits.

## Authoritative sources and provenance

ICMR-NIN Nutrient Requirements for Indians RDA/EAR 2020 is authoritative for Indian targets; Dietary Guidelines for Indians 2024 informs educational wording; IFCT 2017 is the preferred Indian food-composition source. Government or institutional sources such as USDA FoodData Central may fill gaps when license and provenance are recorded. Every value/rule includes source, version, effective date, extraction/transform notes, missingness, and review status. Restricted sources are locally imported and not committed.

## Core model invariants

1. Manual food and ingredient logging is the core input workflow.
2. Logged consumed intake and estimated effective intake are separate first-class states.
3. Nutrition is evaluated daily and over rolling 7-day and 30-day windows.
4. Targets, absorption rules, risk models, and recommendation models are deterministic, transparent, effective-dated, versioned, and reproducible.
5. Historical targets and decision traces are immutable.
6. Missing nutrient values are explicit and never invented.
7. Quantitative absorption changes require reviewed quantitative evidence; qualitative relationships are contextual only.
8. The LLM, when enabled, receives computed facts and may rephrase deterministic explanations only. It never calculates, selects, scores, or changes a recommendation. The application works fully without it.
9. PostgreSQL is the transactional and historical store. Neo4j stores cited food–nutrient–substance relationships and is optional to the core workflow.
10. The architecture is a reliable modular monolith: FastAPI backend, pure Python domain package, Celery workers, and a primary Flutter client.

## Functional capabilities

### Identity, privacy, and administration

Registration and login use secure password hashing, short-lived JWT access tokens, rotating/revocable refresh tokens, backend RBAC, consent records, and audit events. Demo accounts are local only. Admin actions affecting science, access, or exports are audited. Research exports exclude direct identifiers and apply documented re-identification controls.

### Profiles and targets

Student/Adult users create a minimal profile containing only scientifically required demographic inputs. Target selection produces an immutable snapshot with source, formula/table key, completeness, provisional flag, model version, and trace. Unsupported medical or physiological adjustments remain disabled/informational.

### Foods and meals

Users search curated foods and log meals as ingredient quantities. Food composition includes canonical identifiers/units, serving and edible-portion semantics, source version, and explicit missingness. Optional barcode, OCR, image, and price integrations cannot corrupt or block manual logging.

### Effective-intake estimation

Each estimate returns consumed amount, applied rules, intermediate values, final estimated effective amount, citations, warnings, and model version. Rules have nutrient, enhancer/inhibitor, timing scope, direction, bounded formula, applicability, evidence strength, citation, review state, and effective dates. The engine prevents duplicate application, negative totals, unbounded factors, out-of-scope rules, and silent conflicts.

### Nutritional memory and risk

The twin stores/recomputes daily effective intake, rolling 7-day/30-day coverage, gap/surplus duration, trends, adherence, and valid upper-limit exposure. Meal edits/deletions trigger idempotent recomputation. Risk is an explainable intake-gap indication, never a diagnosis, and exposes normalized factor contributions and model version.

### Recommendations and optimization

Candidate ranking rejects allergies, dietary restrictions, valid upper limits, required ingredient availability, maximum budget, and prep-time constraints. Soft objectives include gap coverage, cost, pantry use, preference, time, waste, sustainability, and variety. Normalized objectives, weights, hard checks, scores, and rejection reasons are persisted.

OR-Tools CP-SAT constructs meals from a bounded food/serving subset with deterministic seeds, time limits, infeasibility handling, fallback, and a full decision trace. Grocery optimization later uses OR-Tools Linear Solver. Deterministic explanations are assembled from stored traces.

### Pantry and simulation

Pantry and grocery features manage quantities, units, expiries, budgets, manual/uploaded prices, shopping lists, substitutions, and expiry-aware suggestions. What-if simulation projects intake coverage and the system’s risk score only. It reports scenario, baseline, assumptions, horizon, weekly results, affected nutrients, model version, and limitations; it does not model clinical outcomes or undocumented depletion.

### Knowledge graph and research support

Neo4j represents cited Food, Nutrient, Substance, and Physiological Outcome nodes with provenance-bearing `CONTAINS`, `HELPS`, `IMPROVES`, and `REDUCES` edges. Graph downtime degrades gracefully. Research baseline mode supplies protocols, synthetic fixtures, schemas, and analysis scripts; it must never imply a participant study occurred without ethics approval and consent.

### Clients

Flutter is the primary client for onboarding/consent, authentication, profile, search/logging, dashboard/trends, recommendations/traces, pantry/grocery, simulation, and appropriate Admin screens. Consumed, estimated effective, target, risk, simulation, and medical disclaimer states must be visibly distinct. The optional Next.js client is deferred.

## Security and quality requirements

Implement secure hashing, expiry/revocation, RBAC, validation, parameterized access, safe CORS, rate-limit-ready auth boundaries, safe upload limits, audit trails, minimal sensitive data, consent, anonymization, log redaction, dependency and secret scanning. Threats include auth abuse, rule tampering, poisoning, upload attacks, prompt injection, re-identification, and provenance loss.

Testing includes domain/golden/conversion/invariant/property tests, optimizer feasible/infeasible tests, API/RBAC/migration/data-pipeline/Celery/Neo4j/Flutter tests, an automated demo, LLM-disabled tests, and optional-integration failure tests. Core domain coverage target is at least 80% with meaningful assertions.

## Delivery order and definition of done

Delivery follows phases 0–9 documented in `PLANS.md`, prioritizing a verified manual backend vertical slice before optional integrations or polished clients. Completion requires reproducible startup, clean migrations/seeds, Student/Adult workflow, Admin science inspection/versioning, full traces, distinct intake states, provenance, optional-service independence, passing checks, license/secret hygiene, honest status documentation, an exact validation report, demo workflow, and a complete README.

