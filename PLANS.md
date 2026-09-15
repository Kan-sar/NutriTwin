# NutriTwin delivery plan

Updated: 2026-09-15. This is the current phase-level plan; [the original plan](docs/archive/DELIVERY_PLAN_2026-08-31.md) is retained for history.

The historical 70% convention means seven accepted phase gates, not a percentage of code written. Engineering tests cannot substitute for lawful scientific inputs and independent review. The current implementation does not yet meet that scientific acceptance gate.

| Phase | Scope | Current status and remaining gate |
|---|---|---|
| 0 | Specification, architecture, provenance, safety and traceability | Implemented; active decisions reconciled in ADR 0006 |
| 1 | API, authentication/RBAC, consent, audit, migrations, Compose and CI | Implemented and exercised locally; production operations remain outside scope |
| 2 | Manual profile, food, journal, twin and explanation workflow | Implemented with explicitly synthetic targets |
| 2A | ChEBI/FoodOn and qualitative evidence | Implemented for the bounded, calculation-inactive subset |
| 3 | Licensed ICMR targets and reference golden cases | Import and review infrastructure implemented; lawful inputs and independent scientific fixtures missing |
| 4 | Reviewed quantitative effective-intake rules | Separate Admin approval and scoped runtime implemented; real approved evidence and golden cases missing |
| 5 | Materialized history and scheduled recomputation | Implemented with PostgreSQL job traces, durable dispatch, retries and consent checks; load/concurrency hardening remains |
| 6 | Ranking and CP-SAT meal construction | Demo workflow implemented; real-input path gated; real recipe ranking and scientific acceptance incomplete |
| 7 | Pantry, groceries and deterministic what-if | Deferred |
| 8 | Evidence graph, Admin tools and research export | Scientific review and inspection implemented; graph authoring and research export deferred |
| 9 | Flutter and client hardening | Manual Flutter Web workflow implemented; native packaging, offline sync, additional locales and broader accessibility work remain |

## Next acceptance work

1. Acquire permitted ICMR-NIN 2020 inputs and independently reviewed reference/golden cases through the local scientific handoff.
2. Review quantitative evidence for defined ingredient, meal and timing scopes; activate only source-supported versions.
3. Finish real recipe ranking and test real-data planning against the reviewed references.
4. Exercise concurrent edits, prolonged worker recovery, and native Flutter packaging/accessibility.
5. Only then extend pantry, groceries, simulations, graph editing and aggregate research export.

The current scope uses Student, Adult and Admin roles. Pregnancy/lactation, disease, medications and supplements remain unsupported. Redis, Neo4j, external APIs and LLMs cannot be required for the manual core. No licensed publication is bundled, and no synthetic value may be described as an ICMR value.

See [ADR 0006](docs/adr/0006-reviewed-science-and-seventy-percent-scope.md), [validation](docs/VALIDATION_REPORT.md), [traceability](docs/REQUIREMENTS_TRACEABILITY_MATRIX.md), and the [dated implementation checkpoint](docs/DEVELOPMENT_PROGRESS_2026-09-14.md).
