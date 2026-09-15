"""Acceptance cases use fictional review data solely inside isolated test databases."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from nutritwin_api.models import (
    DataSource,
    Food,
    Profile,
    RecomputeJob,
    Role,
    ScientificRevision,
    User,
)
from nutritwin_api.services.recompute import (
    ensure_recompute_job,
    execute_recompute_job,
    input_revision_for_day,
)
from nutritwin_api.services.science import EffectivePayload, TargetPayload
from nutritwin_api.services.targets import age_in_years, historical_profile
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker


def headers(client: TestClient, admin: bool = False) -> dict[str, str]:
    result = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@example.com" if admin else "student@example.com",
            # pragma: allowlist nextline secret -- public seeded local demo accounts
            "password": "AdminDemo!2026" if admin else "StudentDemo!2026",
        },
    )
    assert result.status_code == 200
    return {"Authorization": "Bearer " + result.json()["access_token"]}


def profile(client: TestClient, h: dict[str, str]) -> None:
    r = client.put(
        "/api/v1/profiles/me",
        headers=h,
        json={
            "birth_date": "2000-01-01",
            "dietary_pattern": "vegetarian",
            "allergens": [],
        },
    )
    assert r.status_code == 200, r.text


def food(client: TestClient, h: dict[str, str], code: str, query: str) -> str:
    return next(
        f["id"]
        for f in client.get("/api/v1/foods", headers=h, params={"query": query}).json()
        if f["food_code"] == code
    )


def log(
    client: TestClient, h: dict[str, str], food_id: str, on: date | None = None, hour: int = 12
) -> dict:
    on = on or date.today()
    payload = {
        "name": "Acceptance meal",
        "local_date": on.isoformat(),
        "eaten_at": datetime.combine(on, datetime.min.time(), tzinfo=UTC)
        .replace(hour=hour)
        .isoformat(),
        "ingredients": [{"food_id": food_id, "quantity_g": "100"}],
    }
    r = client.post("/api/v1/meals", headers=h, json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def test_preferences_change_hard_filter_and_history_is_owner_scoped(client: TestClient) -> None:
    h = headers(client)
    profile(client, h)
    assert client.get("/api/v1/preferences", headers=h).json()["maximum_preparation_minutes"] == 30
    preferences = {"weights": {"preparation_time": "1"}, "maximum_preparation_minutes": 6}
    assert client.put("/api/v1/preferences", headers=h, json=preferences).status_code == 200
    ranked = client.get("/api/v1/recommendations", headers=h).json()
    assert len(ranked["recommendations"]) == 1
    assert ranked["recommendations"][0]["candidate_id"] == "demo-yogurt-orange-bowl"
    assert all("preparation_time" in r["rejection_reasons"] for r in ranked["rejected_candidates"])
    saved = client.get("/api/v1/recommendations/history", headers=h).json()
    assert len(saved) == 3
    decision = saved[0]["id"]
    explanation = client.get(f"/api/v1/recommendations/{decision}/explain", headers=h).json()
    assert explanation["llm_used"] is False
    assert explanation["trace"]["normalized_weights"] == {"preparation_time": "1"}
    assert (
        client.get(
            f"/api/v1/recommendations/{decision}/explain", headers=headers(client, True)
        ).status_code
        == 404
    )
    compact = client.get(
        f"/api/v1/recommendations/{decision}/explain?format=compact", headers=h
    ).json()
    assert compact["trace"] is None
    preferences["weights"] = {"unsupported": "1"}
    assert client.put("/api/v1/preferences", headers=h, json=preferences).status_code == 422


def test_manual_prices_are_private_and_real_planning_requires_review(client: TestClient) -> None:
    h = headers(client)
    profile(client, h)
    fid = food(client, h, "usda-fdc-2644283", "lentils")
    payload = {
        "cost_minor_per_100g": 1200,
        "currency": "INR",
        "preparation_minutes": 25,
        "maximum_servings": 2,
        "observed_on": (date.today() - timedelta(days=15)).isoformat(),
    }
    assert client.put(f"/api/v1/food-offers/{fid}", headers=h, json=payload).status_code == 200
    assert client.get("/api/v1/food-offers", headers=h).json()[0]["stale_pricing"] is True
    assert client.get("/api/v1/food-offers", headers=headers(client, True)).json() == []
    payload["observed_on"] = date.today().isoformat()
    payload["cost_minor_per_100g"] = 1000
    assert client.put(f"/api/v1/food-offers/{fid}", headers=h, json=payload).status_code == 200
    saved = client.get("/api/v1/food-offers", headers=h).json()
    assert len(saved) == 1 and saved[0]["cost_minor_per_100g"] == 1000
    payload["observed_on"] = (date.today() + timedelta(days=1)).isoformat()
    assert client.put(f"/api/v1/food-offers/{fid}", headers=h, json=payload).status_code == 422
    request = {"demo_mode": False, "nutrient_minimums": {"iron": "1"}, "maximum_budget_minor": 5000}
    result = client.post("/api/v1/recommendations/construct", headers=h, json=request)
    assert result.status_code == 409
    assert "authoritative targets" in result.text


def test_partial_food_composition_is_not_complete_and_registry_is_visible(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    h = headers(client)
    profile(client, h)
    lentil = food(client, h, "demo-lentils-cooked", "lentils")
    orange = food(client, h, "demo-orange-raw", "orange")
    with session_factory() as db:
        row = next(n for n in db.get(Food, UUID(orange)).nutrients if n.nutrient.code == "iron")
        row.amount_per_100g = None
        row.value_status = "missing"
        row.missing_reason = "not_reported"
        db.commit()
    log(client, h, lentil)
    log(client, h, orange)
    result = client.get("/api/v1/twin/summary", headers=h)
    assert result.status_code == 200, result.text
    nutrients = {n["nutrient_code"]: n for n in result.json()["nutrients"]}
    assert len(nutrients) == 12
    assert nutrients["iron"]["consumed"]["daily"]["total_amount"] == "3.0000"
    assert nutrients["iron"]["composition_complete_today"] is False
    assert nutrients["iron"]["risk"]["data_complete"] is False
    assert nutrients["zinc"]["target"]["rda"] is None
    assert nutrients["zinc"]["consumed"]["daily"]["total_amount"] is None


def test_moving_meal_invalidates_both_windows_and_preserves_completed_trace(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    h = headers(client)
    profile(client, h)
    fid = food(client, h, "demo-lentils-cooked", "lentils")
    today = date.today()
    meal = log(client, h, fid, today - timedelta(days=2))
    original = client.get("/api/v1/twin/summary", headers=h).json()
    uid = UUID(client.get("/api/v1/users/me", headers=h).json()["id"])
    with session_factory() as db:
        prior = db.scalar(
            select(RecomputeJob).where(
                RecomputeJob.user_id == uid,
                RecomputeJob.affected_date == today,
                RecomputeJob.status == "completed",
            )
        )
        prior_id = prior.id
        pending = ensure_recompute_job(db, uid, today - timedelta(days=1))
        pending_id = pending.id
        db.commit()
    payload = {k: meal[k] for k in ("name", "eaten_at", "local_date", "ingredients")}
    payload["local_date"] = today.isoformat()
    payload["eaten_at"] = datetime.now(UTC).isoformat()
    assert client.put(f"/api/v1/meals/{meal['id']}", headers=h, json=payload).status_code == 200
    updated = client.get("/api/v1/twin/summary", headers=h).json()
    iron = next(n for n in updated["nutrients"] if n["nutrient_code"] == "iron")
    assert iron["daily_series"][-1]["consumed"] == "3.0000"
    assert iron["daily_series"][-3]["consumed"] is None
    with session_factory() as db:
        assert execute_recompute_job(db, prior_id) == original
        assert execute_recompute_job(db, pending_id) == {"status": "superseded"}
        assert db.get(RecomputeJob, prior_id).attempts == 1
        before = input_revision_for_day(db, uid, today)
        db.get(Food, UUID(fid)).edible_fraction = Decimal("0.9")
        db.flush()
        assert input_revision_for_day(db, uid, today) != before


def test_calendar_age_and_profile_history(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    assert age_in_years(date(2000, 9, 15), date(2026, 9, 14)) == 25
    assert age_in_years(date(2000, 9, 15), date(2026, 9, 15)) == 26
    with pytest.raises(ValueError):
        age_in_years(date(2030, 1, 1), date(2026, 1, 1))
    h = headers(client)
    profile(client, h)
    old = client.get("/api/v1/profiles/me", headers=h).json()["revision"]
    result = client.put(
        "/api/v1/profiles/me",
        headers=h,
        json={"birth_date": "2001-01-01", "source_sex_category": "female"},
    )
    assert result.status_code == 200
    uid = UUID(client.get("/api/v1/users/me", headers=h).json()["id"])
    with session_factory() as db:
        current = db.scalar(select(Profile).where(Profile.user_id == uid))
        revision, facts = historical_profile(db, current, date.today() - timedelta(days=1))
        assert revision == old and facts["birth_date"] == "2000-01-01"
        assert historical_profile(db, current, date.today())[1]["birth_date"] == "2001-01-01"


def scientific_setup(client: TestClient, factory: sessionmaker[Session]) -> tuple[dict, dict, str]:
    proposer = headers(client, True)
    with factory() as db:
        user = db.scalar(select(User).where(User.email_normalized == "student@example.com"))
        user.role = Role.ADMIN
        source = db.scalar(
            select(DataSource).where(DataSource.code == "USDA-FDC-FOUNDATION-2026-04")
        )
        source_id = str(source.id)
        db.commit()
    return proposer, headers(client), source_id


def proposal_payload(source_id: str, kind: str = "effective") -> dict:
    base = {
        "source_id": source_id,
        "nutrient_code": "iron",
        "version": "fixture-v1",
        "citation": "https://example.org/fictional-test-evidence",
        "scientific_review": "Fictional isolated test fixture; not scientific evidence.",
        "acquisition_permission": "Fictional test data only.",
    }
    if kind == "effective":
        base.update(
            {
                "trigger_food_code": "demo-orange-raw",
                "target_food_codes": ["demo-lentils-cooked"],
                "direction": "enhance",
                "factor": "1.2",
                "minimum_factor": "1",
                "maximum_factor": "1.5",
                "timing_minutes": 60,
                "applicability": "Only fictional lentil and orange fixtures.",
            }
        )
    else:
        base.update(
            {
                "rda": "9",
                "ear": "7",
                "tul": "40",
                "minimum_age": "18",
                "maximum_age_exclusive": "100",
            }
        )
    return {"kind": kind, "effective_from": date.today().isoformat(), "payload": base}


def transition(client: TestClient, h: dict, rid: str, action: str):
    return client.post(
        f"/api/v1/admin/science/revisions/{rid}/review",
        headers=h,
        json={
            "action": action,
            "review_record": "Isolated test approval, not real scientific review.",
        },
    )


def test_two_admin_governance_time_scope_and_retirement(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    student = headers(client)
    assert client.get("/api/v1/admin/science/revisions", headers=student).status_code == 403
    proposer, reviewer, source = scientific_setup(client, session_factory)
    profile(client, reviewer)
    payload = proposal_payload(source)
    result = client.post("/api/v1/admin/science/revisions", headers=proposer, json=payload)
    assert result.status_code == 201, result.text
    rid = result.json()["id"]
    lentil = food(client, reviewer, "demo-lentils-cooked", "lentils")
    orange = food(client, reviewer, "demo-orange-raw", "orange")
    log(client, reviewer, lentil, hour=12)
    trigger = log(client, reviewer, orange, hour=13)

    def amount():
        r = client.get("/api/v1/twin/summary", headers=reviewer)
        assert r.status_code == 200, r.text
        return next(n for n in r.json()["nutrients"] if n["nutrient_code"] == "iron")

    baseline = Decimal(amount()["estimated_effective"]["daily"]["total_amount"])
    assert transition(client, proposer, rid, "approve").status_code == 403
    assert transition(client, reviewer, rid, "activate").status_code == 409
    assert transition(client, reviewer, rid, "approve").status_code == 200
    assert Decimal(amount()["estimated_effective"]["daily"]["total_amount"]) == baseline
    assert transition(client, proposer, rid, "activate").status_code == 200
    changed = amount()
    assert Decimal(changed["estimated_effective"]["daily"]["total_amount"]) == baseline + Decimal(
        "0.6"
    )
    assert Decimal(changed["consumed"]["daily"]["total_amount"]) == baseline
    moved = {k: trigger[k] for k in ("name", "eaten_at", "local_date", "ingredients")}
    moved["eaten_at"] = datetime.now(UTC).replace(hour=14, minute=1).isoformat()
    assert (
        client.put(f"/api/v1/meals/{trigger['id']}", headers=reviewer, json=moved).status_code
        == 200
    )
    assert Decimal(amount()["estimated_effective"]["daily"]["total_amount"]) == baseline
    assert transition(client, proposer, rid, "retire").status_code == 403
    assert transition(client, reviewer, rid, "retire").status_code == 200
    assert transition(client, reviewer, rid, "activate").status_code == 409


def test_reference_target_activation_and_invalid_payloads(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    proposer, reviewer, source = scientific_setup(client, session_factory)
    payload = proposal_payload(source, "target")
    assert (
        client.post("/api/v1/admin/science/revisions", headers=proposer, json=payload).status_code
        == 422
    )
    # Authority is fictional and limited to this rollback-isolated database.
    with session_factory() as db:
        db.get(DataSource, UUID(source)).authoritative = True
        db.commit()
    result = client.post("/api/v1/admin/science/revisions", headers=proposer, json=payload)
    assert result.status_code == 201, result.text
    rid = result.json()["id"]
    assert transition(client, reviewer, rid, "approve").status_code == 200
    assert transition(client, proposer, rid, "activate").status_code == 200
    profile(client, reviewer)
    targets = client.get("/api/v1/targets/current", headers=reviewer).json()
    assert next(v for v in targets["values"] if v["nutrient_code"] == "iron")["rda"] == "9.000000"
    assert targets["provisional"] is True  # Other nutrients remain demo values.
    duplicate = client.post(
        "/api/v1/admin/science/revisions", headers=proposer, json=payload
    ).json()["id"]
    assert transition(client, reviewer, duplicate, "approve").status_code == 200
    assert transition(client, proposer, duplicate, "activate").status_code == 409
    assert transition(client, reviewer, rid, "retire").status_code == 200
    bad = proposal_payload(source)
    bad["effective_from"] = (date.today() - timedelta(days=1)).isoformat()
    assert (
        client.post("/api/v1/admin/science/revisions", headers=proposer, json=bad).status_code
        == 422
    )
    p = bad["payload"]
    p["factor"] = "3"
    with pytest.raises(ValueError):
        EffectivePayload.model_validate(p)
    p = proposal_payload(source, "target")["payload"]
    p["ear"] = "15"
    with pytest.raises(ValueError):
        TargetPayload.model_validate(p)
    with session_factory() as db:
        row = db.get(ScientificRevision, UUID(duplicate))
        row.payload = {**row.payload, "rda": "99"}
        db.commit()
    assert transition(client, proposer, duplicate, "activate").status_code == 409


def test_consent_withdrawal_blocks_meal_mutation(client: TestClient) -> None:
    h = headers(client)
    profile(client, h)
    fid = food(client, h, "demo-lentils-cooked", "lentils")
    meal = log(client, h, fid)
    assert (
        client.post(
            "/api/v1/consents", headers=h, json={"document_version": "test-v1", "granted": False}
        ).status_code
        == 201
    )
    assert client.delete(f"/api/v1/meals/{meal['id']}", headers=h).status_code == 409
    assert client.get("/api/v1/twin/summary", headers=h).status_code == 409
