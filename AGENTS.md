# NutriTwin repository instructions

## Authority and safety

`docs/NUTRITWIN_SPEC.md` is the functional source of truth. The application is an academic, non-diagnostic nutrition prototype. It must never diagnose deficiency, prescribe supplements, recommend medication changes, or describe estimated effective intake as measured absorption.

Only the roles `student`, `adult`, and `admin` are valid. ICMR-NIN 2020 is authoritative for Indian RDA/EAR/TUL records, but restricted source material must not be committed or transcribed without permission. Demo/synthetic records must remain visibly labeled and must not be described as ICMR values.

## Engineering invariants

- Keep consumed intake, estimated effective intake, targets, and simulations distinct in schemas, storage, APIs, and UI.
- Domain calculations live in `packages/domain`; API, ORM, workers, and clients only orchestrate them.
- Use `Decimal` in nutrition calculations and canonical units defined in the nutrient registry.
- Missing nutrient values are `null`/absent, never silently zero.
- Scientific and scoring rules are versioned, effective-dated, deterministic, and return a trace.
- Quantitative absorption rules require an approved citation and bounded factor. Qualitative evidence cannot alter totals.
- Recommendations reject hard-constraint violations before soft scoring. Allergens can never be traded off.
- LLM use is optional rephrasing only and must not affect a number, score, rule, or meal choice.
- Core workflows must remain usable when Redis, Neo4j, external APIs, and any LLM are unavailable.
- Preserve historical targets and calculation traces. Never mutate an effective historical version.

## Workflow

Before editing: inspect `git status`, relevant ADRs, and `PLANS.md`. Add or update meaningful tests with changes. Run the narrow tests first, then `make check`. Update `docs/VALIDATION_REPORT.md` with commands actually run; do not claim unexecuted checks. Preserve unrelated user work and never commit secrets, private inputs, or restricted publications.

Before adding an external repository, package, ontology, or dataset, apply the intake
policy in `THIRD_PARTY_NOTICES.md`: official upstream only, pinned version/commit,
license and redistribution review, provenance entry, security checks, and no copied
code unless its license and necessity are explicitly documented.

## Status vocabulary

- **Implemented**: exercised by a passing automated test or verified command.
- **Partial**: some usable behavior exists, with documented gaps.
- **Stubbed**: interface exists but intentionally returns a safe placeholder/unavailable result.
- **Deferred**: no implementation is claimed.
