# ADR 0006: Reviewed science, historical calculations, and the 70% implementation scope

Status: Accepted for implementation, 2026-09-14. Scientific acceptance remains conditional.

The implementation follows the reviewed project plan and current Student/Adult/Admin scope. Earlier SRS variants contain incompatible score direction, target fallbacks, and optimizer fallback descriptions. The existing v1 risk formula is retained for reproducibility: larger scores indicate a more persistent logged intake gap; missing logging contributes uncertainty, not evidence of a deficiency. Formula changes require a separately versioned model and review.

## Decisions

- Preserve v1 traces. New summaries use twin-summary-v2 and target snapshots include the reference fingerprint, profile revision, and calculation date. Completed job traces remain immutable; changed dependencies create a new revision.
- Rolling coverage divides known totals by the sum of each day's applicable targets. Unknown composition and missing dates remain explicit. An incomplete total is a lower bound. Zero is not missing. Upper-limit exposure uses consumed intake against each day's applicable limit.
- Profile facts are effective-dated. The first recorded profile is a user-provided baseline assumption for earlier journal dates; later changes apply from their recorded effective date. This is not independently verified historical demographic evidence.
- Scientific proposals are immutable and checksum-bearing. A different Admin must approve or reject; activation is explicit. New versions cannot be backdated. Retirement is effective from its recorded date, with completed calculation traces preserved. Qualitative evidence never enters quantitative calculations.
- Each quantitative rule requires registered source provenance, citation, acquisition permission, scientific-review record, bounded factor, ingredient applicability, and a maximum 120-minute timing scope. Isolated tests use fictional values. No test fixture is seeded as real evidence.
- The local importer validates acquired-file SHA-256 and canonical units, defaults to rollback, and only submits records. It cannot approve or activate. Restricted inputs belong in ignored data/private or outside the repository.
- CP-SAT v2 enforces nutrient minima, upper limits, allergens, diet, budget, preparation, and serving bounds. Conservative integer rounding and Decimal post-validation prevent rounding from concealing a violation. Infeasible/unfinished solves return no compliant meal; hard constraints are never silently relaxed. Cost and serving count are the optimization objectives.
- Real construction requires reviewed authoritative targets, relevant complete logged composition, source-backed foods, and fresh owner-entered INR prices. Demo templates and prices remain explicitly synthetic. Saved preference weights affect template ranking; ranked real recipe generation remains incomplete.
- PostgreSQL RecomputeJob.result_trace is the materialized memory store for daily series, rolling coverage, and score contributions. Separate duplicate daily-total tables are unnecessary for this bounded prototype. Meal edits enqueue all affected windows, including both dates when moved. Celery beat drains durable jobs and creates daily work; API reads can calculate without Redis. Failed jobs have bounded retries, and withdrawn consent cancels pending background work.
- Flutter Web brings the manual workflow forward from phase 9. Android/iOS packaging, offline synchronization, broader accessibility certification, pantry, groceries, what-if simulations, graph authoring, and research export remain deferred.

## Acceptance

The historical convention calls seven completed phase gates 70%. Engineering infrastructure cannot substitute for lawful ICMR fixtures and independent scientific review. Accordingly, do not label this working tree as a scientifically accepted 70% release. Current evidence is recorded in DEVELOPMENT_PROGRESS_2026-09-14.md and VALIDATION_REPORT.md.
