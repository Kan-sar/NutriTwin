> Resolved 2026-09-14: repeated Flutter version checks were fetching the full Git tag history. The tool snapshot was generated successfully with --no-version-check. Flutter Web now builds and runs. See apps/mobile/README.md. The prior stalled state below is historical.

# Flutter setup handoff

Updated: 2026-08-31

Status: **paused at a safe, resumable checkpoint**. The Flutter application source has
not been generated or edited yet.

## Completed setup

- Cloned the official Flutter stable repository to `C:\apps\flutter` with a shallow
  `stable` checkout.
- Installed Flutter framework version `3.47.2` at commit
  `d3b14c876900e553bc736ca19295fc09e3853e8e`.
- Downloaded and extracted Dart SDK `3.13.2` for `windows_x64`.
- Completed the Flutter tool's package dependency resolution.
- Added `C:\apps\flutter\bin` to the current user's persistent `PATH`.
- Verified the standalone Dart executable with `dart --version`.
- Confirmed that Chrome is installed. Android Studio, the Android SDK, Java, and
  Visual Studio build tools are not installed.
- Inspected the official MyPlate flat food-group visual system and the USDA ERS
  Tableau Public nutrition dashboard as design references. No MyPlate logo, brand
  asset, or U.S. dietary value has been copied into the application.

## Pause reason

The first `flutter` command downloaded Dart and resolved dependencies, then stopped
making progress while compiling `bin/cache/flutter_tools.snapshot`. The Dart VM used
no CPU for several minutes, so the bootstrap command was interrupted. The large SDK
downloads remain intact and will not need to be repeated.

Verified checkpoint:

- `C:\apps\flutter\.git` exists.
- `C:\apps\flutter\bin\cache\dart-sdk\bin\dart.exe` exists and runs.
- `C:\apps\flutter\bin\cache\flutter_tools.snapshot` does not yet exist.
- No Flutter or Dart bootstrap process remains active.
- The zero-byte `flutter.bat.lock` file is harmless when no process holds it; Flutter
  acquires the file handle on the next run.

## Resume commands

Open a new PowerShell window so the persisted PATH is loaded, then run:

```powershell
$env:PATH = "C:\apps\flutter\bin;$env:PATH"
& 'C:\apps\flutter\bin\cache\dart-sdk\bin\dart.exe' --version
& 'C:\apps\flutter\bin\flutter.bat' --version -v
```

If the Flutter tool snapshot completes, continue with:

```powershell
flutter config --no-analytics --enable-web
dart --disable-analytics
flutter doctor -v
flutter create --org com.nutritwin --project-name nutritwin_mobile `
  --platforms=android,web apps/mobile
```

Run the `flutter create` command from `C:\Projects\NutriTwin`. Preserve this handoff
and replace the current mobile README only when the real client source is ready.

The first validation sequence should be:

```powershell
Set-Location C:\Projects\NutriTwin\apps\mobile
flutter pub get
flutter analyze
flutter test
flutter build web `
  --dart-define=NUTRITWIN_API_BASE_URL=http://127.0.0.1:8000
```

Android compilation will remain unavailable until the official Android Studio/SDK
and Java toolchain are installed and `flutter doctor --android-licenses` succeeds.
Flutter Web can be used first to compile and visually verify the shared Flutter UI.

## Planned client scope

The first implementation should use the real `/api/v1` contract and include:

1. Login, token handling, consent, and Student/Adult profile onboarding.
2. A Tableau-inspired dashboard with one-day, seven-day, and thirty-day filters,
   color-keyed nutrient bars, a visible 100% target reference, and clear data-quality
   labels.
3. Visually separate target, consumed, and estimated-effective values.
4. Manual food search and ingredient-level meal logging.
5. Transparent intake-gap risk factors and the non-diagnostic disclaimer.
6. Recommendation cards with hard-constraint results, scores, rejection reasons, and
   deterministic explanations.
7. Loading, empty, validation, API-error, and offline states.
8. Accessible labels, scalable text, keyboard traversal for web, and widget tests.

The MyPlate inspiration is limited to approachable flat color grouping, simple
educational cards, and clear food/nutrition hierarchy. NutriTwin must retain its own
name, visual identity, Indian-source governance, and non-clinical terminology.
