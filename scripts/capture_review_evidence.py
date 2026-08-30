"""Capture reproducible, secret-safe Review-1 evidence from a running local API."""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib
import json
import shutil
import subprocess
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, cast

import httpx
from nutritwin_api.config import get_settings
from nutritwin_api.database import create_database_engine, create_session_factory
from nutritwin_api.models import (
    AuditEvent,
    ChemicalSubstance,
    DataSource,
    FoodOntologyMapping,
    Meal,
    QualitativeInteractionEvidence,
    TargetSnapshot,
)
from sqlalchemy import func, select


def _json(response: httpx.Response) -> dict[str, Any] | list[Any]:
    response.raise_for_status()
    return cast("dict[str, Any] | list[Any]", response.json())


def _login(client: httpx.Client, email: str, password: str) -> dict[str, str]:
    tokens = _json(client.post("/api/v1/auth/login", json={"email": email, "password": password}))
    assert isinstance(tokens, dict)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _git_revision() -> str:
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git is required to record the evidence revision")
    completed = subprocess.run(
        [git, "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _safe_twin(summary: dict[str, Any]) -> dict[str, Any]:
    nutrients: list[dict[str, Any]] = []
    for item in summary["nutrients"]:
        if item["nutrient_code"] not in {"iron", "vitamin_c"}:
            continue
        nutrients.append(
            {
                "nutrient": item["nutrient_code"],
                "unit": item["unit"],
                "target_rda": item["target"]["rda"],
                "consumed": {
                    window: {
                        "total_amount": item["consumed"][window]["total_amount"],
                        "coverage_percent": item["consumed"][window]["coverage_percent"],
                    }
                    for window in ("daily", "rolling_7_day", "rolling_30_day")
                },
                "estimated_effective": {
                    window: {
                        "total_amount": item["estimated_effective"][window]["total_amount"],
                        "coverage_percent": item["estimated_effective"][window]["coverage_percent"],
                    }
                    for window in ("daily", "rolling_7_day", "rolling_30_day")
                },
                "effective_rule": item["estimated_effective"]["calculation_trace"][0]["warnings"],
                "risk": {
                    "score": item["risk"]["score"],
                    "band": item["risk"]["band"],
                    "wording": item["risk"]["wording"],
                    "model_version": item["risk"]["model_version"],
                },
            }
        )
    return {
        "as_of_date": summary["as_of_date"],
        "target_provisional": summary["target_provisional"],
        "logged_days_30": summary["logged_days_30"],
        "nutrients": nutrients,
        "medical_disclaimer": summary["medical_disclaimer"],
    }


def _safe_recommendations(payload: dict[str, Any]) -> dict[str, Any]:
    accepted = payload["recommendations"][0]
    rejected = payload["rejected_candidates"]
    return {
        "model_version": payload["model_version"],
        "llm_used": payload["llm_used"],
        "top_recommendation": {
            "candidate_id": accepted["candidate_id"],
            "score": accepted["score"],
            "hard_constraint_results": accepted["hard_constraint_results"],
            "normalized_objectives": accepted["normalized_objectives"],
            "normalized_weights": accepted["normalized_weights"],
            "explanation": accepted["explanation"],
        },
        "rejected_candidates": [
            {
                "candidate_id": item["candidate_id"],
                "rejection_reasons": item["rejection_reasons"],
            }
            for item in rejected
        ],
        "notice": payload["notice"],
    }


def _database_snapshot() -> dict[str, Any]:
    settings = get_settings()
    engine = create_database_engine(settings.database_url)
    factory = create_session_factory(engine)
    with factory() as session:
        counts = {
            "data_sources": session.scalar(select(func.count()).select_from(DataSource)),
            "target_snapshots": session.scalar(select(func.count()).select_from(TargetSnapshot)),
            "meals": session.scalar(select(func.count()).select_from(Meal)),
            "audit_events": session.scalar(select(func.count()).select_from(AuditEvent)),
            "chemical_substances": session.scalar(
                select(func.count()).select_from(ChemicalSubstance)
            ),
            "food_ontology_mappings": session.scalar(
                select(func.count()).select_from(FoodOntologyMapping)
            ),
            "qualitative_evidence": session.scalar(
                select(func.count()).select_from(QualitativeInteractionEvidence)
            ),
        }
        sources = session.scalars(select(DataSource.code).order_by(DataSource.code)).all()
        substances = session.scalars(
            select(ChemicalSubstance.chebi_id).order_by(ChemicalSubstance.chebi_id)
        ).all()
        return {
            "database_engine": engine.dialect.name,
            "row_counts": counts,
            "source_codes": list(sources),
            "reviewed_chemical_ids": list(substances),
            "privacy_note": (
                "Counts and public reference identifiers only; no user identifiers shown."
            ),
        }


def _run_test_evidence() -> tuple[str, str]:
    command = [
        sys.executable,
        "-m",
        "pytest",
        "--cov",
        "--cov-report=term",
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (completed.stdout + "\n" + completed.stderr).strip()
    if completed.returncode != 0:
        raise RuntimeError(
            f"test evidence command failed with exit {completed.returncode}\n{output}"
        )
    lines = output.splitlines()
    return " ".join(command), "\n".join(lines[-55:])


def _evidence_html(title: str, source: str, payload: Any) -> str:
    pretty = json.dumps(payload, indent=2, ensure_ascii=True, default=str)
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
body {{ margin: 0; background: #07111f; color: #d9e6f2;
  font-family: Segoe UI, Arial, sans-serif; }}
header {{ padding: 28px 36px 20px; background: linear-gradient(120deg,#0f2742,#123d52);
  border-bottom: 3px solid #2bc6a4; }}
h1 {{ margin: 0 0 8px; font-size: 28px; color: white; }}
.source {{ color: #9fc6d8; font-size: 15px; }}
.badge {{ display:inline-block; margin-top:12px; padding:6px 10px;
  border:1px solid #2bc6a4; border-radius:999px; color:#72e2ca; font-size:13px; }}
main {{ padding: 26px 36px 34px; }}
pre {{ margin:0; padding:22px; border-radius:12px; background:#0b1828;
  border:1px solid #243b52; color:#d6e7f5; font: 15px/1.45 Consolas, monospace;
  white-space:pre-wrap; overflow-wrap:anywhere; }}
footer {{ padding: 0 36px 26px; color:#7594aa; font-size:12px; }}
</style></head><body>
<header><h1>{html.escape(title)}</h1>
<div class="source">{html.escape(source)}</div>
<div class="badge">LIVE LOCAL DEMO EVIDENCE</div></header>
<main><pre>{html.escape(pretty)}</pre></main>
<footer>NutriTwin is non-diagnostic. Synthetic demonstration values are not nutrition
guidance.</footer>
</body></html>"""


def _capture_html(page: Any, output: Path, title: str, source: str, payload: Any) -> None:
    page.set_content(_evidence_html(title, source, payload), wait_until="load")
    page.screenshot(path=str(output), full_page=True)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--output-dir", type=Path, default=Path("docs/review1/evidence"))
    parser.add_argument(
        "--browser-executable",
        type=Path,
        help="Optional Chromium-family executable; Windows falls back to installed Edge/Chrome.",
    )
    args = parser.parse_args()
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    revision = _git_revision()
    captured_at = datetime.now(UTC).replace(microsecond=0).isoformat()

    with httpx.Client(base_url=args.base_url, timeout=30) as client:
        health = _json(client.get("/health/ready"))
        assert isinstance(health, dict)
        student = _login(client, "student@example.com", "StudentDemo!2026")
        admin = _login(client, "admin@example.com", "AdminDemo!2026")

        profile_response = client.get("/api/v1/profiles/me", headers=student)
        if profile_response.status_code == 404:
            _json(
                client.put(
                    "/api/v1/profiles/me",
                    headers=student,
                    json={
                        "birth_date": "2000-01-01",
                        "dietary_pattern": "vegetarian",
                        "allergens": ["milk"],
                    },
                )
            )
        else:
            profile_response.raise_for_status()

        foods = _json(client.get("/api/v1/foods", params={"query": "lentils"}, headers=student))
        assert isinstance(foods, list) and foods
        today = date.today().isoformat()
        meal = _json(
            client.post(
                "/api/v1/meals",
                headers=student,
                json={
                    "name": "Review-1 evidence meal",
                    "eaten_at": datetime.now(UTC).isoformat(),
                    "local_date": today,
                    "ingredients": [{"food_id": foods[0]["id"], "quantity_g": "100"}],
                },
            )
        )
        assert isinstance(meal, dict)
        summary = _json(
            client.get("/api/v1/twin/summary", params={"as_of": today}, headers=student)
        )
        recommendations = _json(
            client.get("/api/v1/recommendations", params={"as_of": today}, headers=student)
        )
        chemistry = _json(client.get("/api/v1/admin/substances", headers=admin))
        evidence = _json(client.get("/api/v1/admin/evidence", headers=admin))
        assert all(
            isinstance(item, dict) for item in (summary, recommendations, chemistry, evidence)
        )
        summary_dict = cast("dict[str, Any]", summary)
        recommendations_dict = cast("dict[str, Any]", recommendations)
        chemistry_dict = cast("dict[str, Any]", chemistry)
        evidence_dict = cast("dict[str, Any]", evidence)

        workflow = {
            "health": health,
            "authenticated_role": "student",
            "food_search_result": {
                "food_code": foods[0]["food_code"],
                "authoritative": foods[0]["authoritative"],
            },
            "meal_created": {
                "name": meal["name"],
                "local_date": meal["local_date"],
                "revision": meal["revision"],
                "ingredient_count": len(meal["ingredients"]),
            },
            "status": "successful",
        }
        chemistry_safe = {
            "model_version": chemistry_dict["model_version"],
            "notice": chemistry_dict["notice"],
            "substances": chemistry_dict["substances"],
            "food_mappings": chemistry_dict["food_mappings"],
            "qualitative_evidence": evidence_dict["evidence"],
            "evidence_notice": evidence_dict["notice"],
        }
        test_command, test_output = _run_test_evidence()
        database = _database_snapshot()

        playwright_api = importlib.import_module("playwright.sync_api")
        browser_executable: Path | None = args.browser_executable
        if browser_executable is None and sys.platform == "win32":
            for candidate in (
                Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
                Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            ):
                if candidate.is_file():
                    browser_executable = candidate
                    break
        if browser_executable is not None and not browser_executable.is_file():
            raise RuntimeError(f"browser executable does not exist: {browser_executable}")
        manifest_rows: list[dict[str, str]] = []
        browser_version = "unknown"
        with playwright_api.sync_playwright() as playwright:
            launch_options: dict[str, Any] = {"headless": True}
            if browser_executable is not None:
                launch_options["executable_path"] = str(browser_executable)
            browser = playwright.chromium.launch(**launch_options)
            browser_version = browser.version
            page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)

            swagger_path = output_dir / "01-api-interface.png"
            page.goto(f"{args.base_url}/docs", wait_until="networkidle")
            page.locator(".swagger-ui").wait_for(state="visible")
            page.screenshot(path=str(swagger_path), full_page=True)

            captures = [
                (
                    "02-health-workflow.png",
                    "Successful health and manual workflow",
                    "GET /health/ready; authenticated food search and POST /api/v1/meals",
                    workflow,
                ),
                (
                    "03-nutrition-twin.png",
                    "Consumed and estimated-effective nutrition twin",
                    "GET /api/v1/twin/summary",
                    _safe_twin(summary_dict),
                ),
                (
                    "04-recommendation-trace.png",
                    "Deterministic recommendation decision trace",
                    "GET /api/v1/recommendations",
                    _safe_recommendations(recommendations_dict),
                ),
                (
                    "05-chemistry-evidence.png",
                    "Provenance-bearing nutrition chemistry references",
                    "GET /api/v1/admin/substances and /api/v1/admin/evidence",
                    chemistry_safe,
                ),
                (
                    "06-automated-tests.png",
                    "Automated test and coverage result",
                    test_command,
                    {"command": test_command, "output": test_output},
                ),
                (
                    "07-database-state.png",
                    "Database state with scientific provenance records",
                    "Read-only SQLAlchemy counts from the configured local database",
                    database,
                ),
            ]
            for filename, title, source, payload in captures:
                _capture_html(page, output_dir / filename, title, source, payload)
            browser.close()

        descriptions = {
            "01-api-interface.png": (
                "FastAPI Swagger UI showing the implemented NutriTwin endpoint groups."
            ),
            "02-health-workflow.png": (
                "Successful local readiness check, authenticated food search, and meal creation."
            ),
            "03-nutrition-twin.png": (
                "Iron and vitamin C consumed and estimated-effective totals across three windows."
            ),
            "04-recommendation-trace.png": (
                "Deterministic meal recommendation constraints, score contributions, "
                "and explanation."
            ),
            "05-chemistry-evidence.png": (
                "ChEBI substances, FoodOn mappings, and qualitative evidence with provenance."
            ),
            "06-automated-tests.png": "Passing automated tests and branch-aware coverage output.",
            "07-database-state.png": (
                "Database row counts and public reference identifiers without user identifiers."
            ),
        }
        sources = {
            "01-api-interface.png": "live /docs",
            "02-health-workflow.png": "live local API workflow",
            "03-nutrition-twin.png": "live /api/v1/twin/summary",
            "04-recommendation-trace.png": "live /api/v1/recommendations",
            "05-chemistry-evidence.png": "live Admin chemistry APIs",
            "06-automated-tests.png": test_command,
            "07-database-state.png": "configured local database read-only query",
        }
        for filename in descriptions:
            path = output_dir / filename
            manifest_rows.append(
                {
                    "file": filename,
                    "caption": descriptions[filename],
                    "alt_text": descriptions[filename],
                    "source": sources[filename],
                    "sha256": _sha256(path),
                }
            )
        manifest = {
            "schema_version": "1",
            "application_commit_sha": revision,
            "captured_at": captured_at,
            "base_url": args.base_url,
            "browser": {
                "engine": "Chromium",
                "version": browser_version,
                "executable": (
                    str(browser_executable)
                    if browser_executable is not None
                    else "Playwright bundle"
                ),
            },
            "privacy": (
                "Local demo data only. Tokens, passwords, connection strings, emails, and user IDs "
                "are excluded from the images."
            ),
            "artifacts": manifest_rows,
        }
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        client.delete(f"/api/v1/meals/{meal['id']}", headers=student).raise_for_status()

    print(f"captured {len(manifest_rows)} evidence images in {output_dir}")


if __name__ == "__main__":
    main()
