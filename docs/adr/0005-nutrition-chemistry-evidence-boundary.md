# ADR 0005: Nutrition chemistry references remain non-clinical and calculation-inactive

Status: Accepted - 2026-08-30

## Context

The 30% milestone benefits from stable food and chemical identifiers, but importing
medical repositories or turning qualitative interaction statements into numeric
absorption factors would expand the approved scope and create false precision.

## Decision

NutriTwin stores a small versioned chemistry-reference subset in PostgreSQL:
ChEBI chemical identities, FoodOn mappings, and qualitative nutrient-interaction
evidence. RDKit validates structure metadata in the data pipeline only. Admins receive
read-only provenance-bearing inspection endpoints.

Every qualitative evidence row has calculation_effect=false, enforced both by data
validation and a relational check constraint. These rows are never converted into
effective-intake rules. Medication, condition, dosing, supplement, diagnosis, and
treatment functionality remains excluded.

## Consequences

- Chemical and food identities are normalized without clinical claims.
- The current effective-intake engine remains the explicit identity estimate.
- Optional RDKit installation cannot affect API availability or nutrition results.
- ChEBI/FoodOn attribution and upstream versions remain auditable.
- A future quantitative rule requires a separate reviewed ADR, evidence record, bounded
  model, version, effective date, and golden tests.
