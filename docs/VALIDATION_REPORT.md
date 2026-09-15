# Validation report

## Verified implementation checkpoint

The implementation checkpoint on 2026-09-14 passed **59 backend tests with 82.61% configured branch-aware coverage**, Ruff lint/formatting, mypy, and data validation. RDKit validated the bounded chemistry fixture. The USDA transform contains 74 foods, 751 reported observations and 137 explicit missing values.

Flutter analysis, three client tests and a release Web build passed. A live Chrome run exercised generated-account registration, consent, profile setup, source search, logging, overview, demo ranking, construction and editable draft creation. Desktop and 390-pixel screenshots were inspected. This does not claim that every backend path was browser-tested.

The six-service Compose stack was exercised with PostgreSQL; Alembic reported no schema drift, the worker replied to ping, and scheduler/outbox processing was observed. Docker was subsequently closed at the user's request, preserving volumes. A final image refresh was interrupted during export and is not claimed as verified.

## Repository refresh validation — 2026-09-15

The refreshed repository passed `scripts/check.py`: Ruff lint and formatting (110 files), mypy (52 source files), data validation, 63 local documentation links across 30 Markdown files, and all 59 backend tests with 82.61% coverage. Explicit RDKit validation and `pip-audit` also passed; the local unpublished project is skipped by the package vulnerability index.

Flutter resolved the existing lockfile with `--enforce-lockfile`, passed formatting, analysis and all three tests, and built the release Web client with local Web resources. Compose configuration validation passed without starting Docker. Docker remains closed.

CI now runs the client checks alongside the backend checks using the pinned official Flutter SDK. These are local validation results; published commit-specific CI results are available through the Actions link below.

## Reproducible checks

With the repository Python environment activated:

```sh
python scripts/check.py
python scripts/check_docs.py
python scripts/validate_data.py --require-rdkit
python -m alembic upgrade head
python -m alembic check
```

`check.py` provides the backend checks on systems without GNU Make. `make check` is the equivalent Make entry point. Run Flutter analysis, tests and release Web build from `apps/mobile` using the pinned SDK documented there.

[GitHub Actions](https://github.com/Kan-sar/NutriTwin/actions/workflows/ci.yml) records commit-specific backend and Flutter results. A historical run does not establish that a newer commit passes; inspect the run's commit before citing it.

## Limits and retained evidence

No Android/iOS build, production deployment, comprehensive accessibility certification, load/soak campaign, or real scientific golden-case validation is claimed. ICMR-NIN inputs and quantitative evidence still need lawful acquisition and independent review. The prior build emitted a non-fatal Cupertino font-family warning; rendered Material icons were present.

[Detailed historical validation](archive/VALIDATION_THROUGH_2026-09-14.md) retains the original commands, environment notes, CI identifiers, and recovery/shutdown history. [Review-1 evidence](review1/README.md) remains unchanged and dated. [The delivery plan](../PLANS.md) records the open acceptance gates.
