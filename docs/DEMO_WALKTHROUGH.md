# Demo walkthrough

This walkthrough exercises the implemented manual backend workflow using local synthetic data. It does not demonstrate scientifically validated nutrition guidance.

## Start

After installing, migrating, and seeding as described in the root README, start the API:

```powershell
.venv\Scripts\uvicorn.exe nutritwin_api.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for the interactive OpenAPI UI. Alternatively, run the reproducible automation in another terminal:

```powershell
.venv\Scripts\python.exe scripts\demo.py
```

Expected output:

```text
demo passed: nutrients=4, recommendations=2, llm_used=false
```

The automation logs in as the seeded Student, records consent/profile data if needed, searches for a synthetic lentil food, logs a 100 g ingredient-level meal, fetches the twin summary and recommendations, verifies the no-LLM path, and soft-deletes the temporary meal.

## Manual API sequence

1. `POST /api/v1/auth/login` with a local demo account.
2. Send the access token as `Authorization: Bearer <token>`.
3. `POST /api/v1/consents` with `purpose=core_application`, the current demo document version, and `granted=true`.
4. `PUT /api/v1/profiles/me` with a past birth date and optional dietary pattern/allergens.
5. `GET /api/v1/targets/current`; verify `provisional=true` and inspect its calculation trace.
6. `GET /api/v1/foods?query=lentils`; verify the source is `DEMO-SYNTHETIC` and `authoritative=false`.
7. `POST /api/v1/meals` with a food UUID and positive decimal `quantity_g`.
8. `GET /api/v1/twin/summary?as_of=YYYY-MM-DD`; compare `consumed_amount` and `estimated_effective_amount`, inspect daily/7-day/30-day coverage, completeness, risk factors, model versions, warnings, and disclaimer.
9. `GET /api/v1/recommendations?as_of=YYYY-MM-DD`; inspect accepted and rejected candidates, hard checks, normalized objectives, weights, overall score, deterministic explanation, and `llm_used=false`.
10. `PUT` or `DELETE /api/v1/meals/{id}` and fetch the summary again to observe revision-aware recalculation.

## Admin check

Log in with `admin@example.com` and call `GET /api/v1/admin/reference-data` or `GET /api/v1/admin/audit-events`. A Student or Adult receives HTTP 403 for those routes.

## Interpretation boundary

The demo foods and target values are synthetic. “Estimated effective” is an explicit identity estimate because no quantitative absorption rule is approved. “Persistent intake-gap risk indication” describes the deterministic model output; it is not a diagnosis of deficiency.
