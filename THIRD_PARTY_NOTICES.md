# Third-party notices and open-source intake register

This repository consumes pinned packages, container images, public APIs, and attributed
reference subsets. No third-party repository source code has been copied into NutriTwin.
The requirements lock files, pyproject.toml, and infra/docker/compose.yaml are the
machine-readable dependency inventory; this register records the components and data
resources that materially shape the 30% academic milestone.

## Milestone-specific components and data

| Component | Upstream / pinned reference | License | Use and modifications | Maintenance / security | Limitations |
|---|---|---|---|---|---|
| RDKit | https://github.com/rdkit/rdkit; Release_2026_03_5, commit de8add1e32ff6d3c4e4e406f64b703b662dff1d6; Python package 2026.3.5 | BSD-3-Clause | Optional chem dependency; validates/canonicalizes committed demo SMILES, formula, InChI, and InChIKey. No upstream files modified. | Active 2026 release; included in CI validation and dependency audit | Cheminformatics validation only; no absorption, diagnosis, bioactivity, or treatment prediction |
| ChEBI | https://www.ebi.ac.uk/chebi/; accessed 2026-08-30 | CC BY 4.0 | Two attributed chemical reference records are stored as a small transformed JSON subset. | EMBL-EBI maintained; stable identifiers retained | Chemical identity is not evidence of a nutritional or clinical effect |
| FoodOn | https://github.com/FoodOntology/foodon; ontology version 2025-12-30; maintenance check at commit c5035015de540ba4f4210fd0e24d3909d6fb2037 | CC BY 4.0 | Three reviewed food-to-ontology mappings; no ontology source files copied | OBO/OLS published version and stable PURLs used | Broad mappings are labelled and must not be interpreted as composition equivalence |
| Playwright for Python | https://github.com/microsoft/playwright-python; v1.62.0, commit 3b7c24c3e67dc84f7b0eddd0c5fd2ca685705021 | Apache-2.0 | Optional evidence dependency for local browser screenshots; no upstream files modified | Pinned release; only local loopback pages are captured | Evidence capture tool, not an application runtime dependency |
| NIH ODS Iron Fact Sheet | https://ods.od.nih.gov/factsheets/Iron-HealthProfessional/; accessed 2026-08-30 | US government informational material; attribution retained | Citation metadata for one qualitative vitamin-C/nonheme-iron context record | Living authoritative information page; access version recorded | Informational only and explicitly forbidden from changing calculations |

## Existing framework and infrastructure dependencies

FastAPI, Pydantic, SQLAlchemy, Alembic, Celery, Google OR-Tools, PostgreSQL, Redis,
Neo4j Community Edition, and their transitive dependencies retain their upstream
licenses. Exact package and image versions are pinned in repository manifests. Redis
7.4 is source-available under its upstream terms and is not described here as
OSI-approved open source.

## Intake and review policy

Before adding or upgrading any third-party component:

1. Prefer the official upstream repository, release, documentation, or institutional API.
2. Record the release/tag, commit where available, SPDX license, acquisition date, and
   checksum for downloaded artifacts.
3. Confirm license compatibility before copying or redistributing code or data.
4. Pin the dependency or source version; never depend on an unpinned branch.
5. Run dependency audit, tests, and provenance validation.
6. Treat external medical, chemical, and nutrition content as untrusted input and require
   a separate scientific citation before it can support a rule.
7. Keep qualitative evidence calculation-inactive. A new quantitative rule requires an
   approved citation, bounds, version, effective date, and golden/invariant tests.

The project itself has no selected license. Until the owner adds one, repository-authored
material remains all-rights-reserved; third-party terms continue to apply independently.
