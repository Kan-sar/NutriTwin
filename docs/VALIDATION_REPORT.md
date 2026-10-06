# Validation report

## Meal conflict protection — 2026-09-15

`python scripts/check.py` passed: 62 tests, 82.86% coverage, Ruff, mypy, data/RDKit validation and 63 documentation links. New tests exercise simultaneous claims from two SQLite database sessions, stale edits/deletes, owner isolation, and unchanged audit/outbox records after conflicts. PostgreSQL concurrency was not exercised in this checkpoint; Docker remains closed.

Flutter analysis, all five tests and the release Web build (`--release --no-web-resources-cdn`) passed, including stale edit/delete handling, retained drafts, refreshed meals and submitting the newly loaded revision. The navigation Material surface was corrected after these tests exposed hidden selection/ink effects. The pre-existing non-fatal Cupertino font warning remains.

Meal PUT and DELETE now require the positive `expected_revision` query parameter returned by meal reads. Missing revisions return 422; stale revisions return 409 without changing the meal. The Flutter client and repository scripts send this parameter. Older external clients must be updated. No schema migration is required.

At the usage checkpoint, 95% of the five-hour allowance was consumed. Scientific acceptance, real recipe ranking, PostgreSQL concurrency/worker hardening and native packaging remain open.

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

## Frontend nutrient exploration — 2026-10-06

Adapted interaction patterns from https://www.itsmyplate.com/ in the existing Flutter client, without importing its code or assets. Overview now exposes selectable nutrient bubbles, daily/7-day/30-day coverage, target bars, and focused detail/history. Food search now ranks the current results by a selected nutrient per 100 g and retains composition inspection and draft addition. API-provided coverage is displayed without introducing client nutrition calculations. Unknown values remain unknown, synthetic target notices remain visible, and consumed versus estimated effective intake stays distinct.

Validation performed:
- `flutter --no-version-check test test/nutrient_explorer_test.dart`: 3 passed after fixing bubble text overflow. Covers focus/reset, period switching, over-target/unknown values, narrow layout with 1.3x text, food ordering, and draft selection.
- `flutter --no-version-check analyze`: no issues.
- `flutter --no-version-check test`: 8 passed, including existing authentication and meal-conflict tests.
- `flutter --no-version-check build web`: succeeded. Flutter emitted a font-family warning; the rendered fixture showed readable text and icons.
- `C:\GCC_bin\mingw64\bin\mingw32-make.exe check`: passed Ruff, formatting, mypy, data validation, documentation links, and backend tests (69 passed, 4 PostgreSQL tests skipped because `NUTRITWIN_TEST_POSTGRES_URL` was unset; 82.78% coverage).
- Built a separate ignored synthetic fixture with `flutter --no-version-check build web --target build/explorer_preview.dart --output build/explorer-preview`, served it on loopback, and inspected the rendered desktop view in the browser. Screenshot: `apps/mobile/build/nutrient-redesign-preview.png` (ignored local artifact). This was visual fixture verification, not an authenticated live-data browser test.

No deployment or scientific acceptance is claimed. Existing unrelated backend/documentation changes were preserved.

## Real catalogue integration and Kaggle assessment — 2026-10-06

Implemented the next dataset increment using the existing pinned April 2026 USDA
Foundation archive: 122 foods, 1,223 reported nutrient observations and 241 explicit
missing observations across twelve canonical nutrients. All 74 prior food records and
their source metadata were compared with HEAD and remain identical. Added a food-only
transactional importer that validates the manifest, rejects changed existing observations,
and creates neither demo accounts nor target rules. Demo seeding now reuses this importer.
The authenticated API supports real/demo filters, bounded pagination and source provenance;
Flutter defaults to real foods and supports browsing/loading more results.

Commands and observed results:
- `python scripts/import_fdc_foundation.py`: validated 122 foods / 1,223 reported / 241 missing.
- `python -m pytest tests/data/test_fdc_foundation.py tests/api/test_catalogue.py tests/api/test_vertical_slice.py -q`: 11 passed.
- `C:\GCC_bin\mingw64\bin\mingw32-make.exe check`: passed Ruff, formatting (117 files), mypy (54 source files), data validation, docs, and backend tests. 76 passed / 4 PostgreSQL cases skipped because no test PostgreSQL URL was configured. Coverage 82.90%.
- `flutter --no-version-check analyze`: no issues.
- `flutter --no-version-check test`: 8 passed.
- `flutter --no-version-check build web`: succeeded; existing font-family warning remains.
- `python scripts/import_catalogue.py`: dry run validated; 122 would be inserted, rolled back.
- Backed up the verified local SQLite development database to ignored `data/raw/nutritwin-before-catalogue-2026-10-06.db`, then ran `python scripts/import_catalogue.py --commit`: inserted 122 foods. A second dry run returned zero new foods.
- `python scripts/check_docs.py`: 99 local links across 32 documents passed after adding the assessment.
- `git diff --check`: no whitespace errors.

Kaggle candidate metadata was read using its public dataset API. Version 3 of the
INDB-derived Indian food dataset was downloaded into ignored raw storage and inspected
(1,014 unique dish names, 164 empty cells, no ingredient/allergen fields, damaged folate
unit label). It is an assessed candidate, not an installed or authoritative source.
See `KAGGLE_DATASET_ASSESSMENT.md` for links, checksum and decisions. No ICMR targets or
IFCT tables were replaced, no scientific approval was fabricated, and no deployment was
performed. This increment did not repeat authenticated browser verification.
