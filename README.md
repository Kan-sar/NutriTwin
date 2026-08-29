# NutriTwin

NutriTwin is an explainable, non-clinical personalized-nutrition digital-twin academic prototype for Indian dietary contexts. It keeps logged consumed intake, estimated effective intake, reference targets, persistent intake-gap indications, and what-if projections explicitly separate.

> **Safety:** NutriTwin is educational research software. It does not diagnose nutrient deficiency or disease, measure biological absorption, prescribe supplements, or recommend medication changes. Seek a qualified professional for medical or dietary care.

## Project status

Phase 0 architecture and scientific-data governance are implemented in documentation. Backend foundation and the manual core vertical slice are in progress. Flutter, pantry/grocery, quantitative absorption modifiers, Neo4j Admin authoring, participant research, OCR/vision/barcode, external prices, LLM rephrasing, Next.js, Kubernetes, and deployment are deferred or blocked as detailed in [PLANS.md](PLANS.md).

Authoritative ICMR-NIN tables are **not bundled** because product redistribution permission has not been established. Initial demo target fixtures are conspicuously synthetic and validate software behavior only. See [the source register](docs/DATA_SOURCE_REGISTER.md).

## Intended architecture

```text
Flutter client (primary; deferred locally)
                 |
            FastAPI modular monolith
 auth | profiles | foods | meals | twin | recommendations | admin
                 |
 pure deterministic domain package
                 |
 PostgreSQL (authoritative history) + optional Redis/Celery + optional Neo4j
```

The complete provisional specification is [docs/NUTRITWIN_SPEC.md](docs/NUTRITWIN_SPEC.md), architecture is [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), and calculation formulas are [docs/ALGORITHM_SPECIFICATION.md](docs/ALGORITHM_SPECIFICATION.md).

## Developer workflow

The target commands, added with the implementation foundation, are:

```bash
make bootstrap
make up
make migrate
make seed
make test
make lint
make typecheck
make validate-data
make demo
make down
```

Windows developers without `make` can use the equivalent documented Python/Docker commands. Exact commands actually verified on this machine are recorded in [docs/VALIDATION_REPORT.md](docs/VALIDATION_REPORT.md).

## Local demo accounts

Demo credentials will be emitted by the local-only seeder and documented here only after the authentication workflow is implemented and verified. They must never be used outside local development.

## Provenance and licensing

- ICMR-NIN RDA/EAR 2020 is the required authority for production-quality Indian targets.
- IFCT 2017 is preferred for Indian food composition.
- Restricted publications belong in ignored local input directories and are imported through checksum-recorded scripts.
- USDA FoodData Central may provide attributed CC0 demo/gap data.
- Missing values remain missing; no absent nutrient is silently converted to zero.

## License

No project license has been selected by the user. Until one is added, all rights in repository-authored material remain with the repository owner. Third-party data and citations retain their own terms.

