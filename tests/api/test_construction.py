from datetime import date
from uuid import UUID

from fastapi.testclient import TestClient
from nutritwin_api.models import RecommendationDecision
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker


def _student_headers(client: TestClient) -> dict[str, str]:
    tokens = client.post(
        "/api/v1/auth/login",
        json={
            "email": "student@example.com",
            "password": "StudentDemo!2026",  # pragma: allowlist secret -- demo fixture
        },
    ).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _profile(
    client: TestClient, headers: dict[str, str], dietary_pattern: str = "vegetarian"
) -> None:
    response = client.put(
        "/api/v1/profiles/me",
        headers=headers,
        json={
            "birth_date": "2000-01-01",
            "dietary_pattern": dietary_pattern,
            "allergens": ["milk"],
        },
    )
    assert response.status_code == 200, response.text


def test_constructed_meal_is_traceable_allergen_safe_and_persisted(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    headers = _student_headers(client)
    _profile(client, headers)
    response = client.post(
        "/api/v1/recommendations/construct",
        headers=headers,
        params={"as_of": date.today().isoformat()},
        json={
            "nutrient_minimums": {"iron": "5", "vitamin_c": "10"},
            "maximum_budget_minor": 2000,
            "seed": 17,
            "time_limit_ms": 500,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] in {"optimal", "feasible"}
    assert body["fallback_used"] is False
    assert body["llm_used"] is False
    assert body["total_cost_minor"] <= 2000
    assert float(body["nutrient_totals_canonical_units"]["iron"]) >= 5
    assert float(body["nutrient_totals_canonical_units"]["vitamin_c"]) >= 10
    assert all("yogurt" not in item["food_code"] for item in body["servings"])
    yogurt = next(
        item
        for item in body["trace"]["candidate_checks"]
        if item["food_code"] == "demo-yogurt-plain"
    )
    assert yogurt["selected"] is False
    assert yogurt["rejection_reasons"] == ["allergens"]

    with session_factory() as session:
        decision = session.scalar(
            select(RecommendationDecision).where(
                RecommendationDecision.id == UUID(body["decision_id"])
            )
        )
        assert decision is not None
        assert decision.trace["optimizer"]["seed"] == 17
        assert decision.model_version == "cp-sat-meal-v1"


def test_constructed_meal_returns_explicit_infeasibility_fallback(client: TestClient) -> None:
    headers = _student_headers(client)
    _profile(client, headers)
    response = client.post(
        "/api/v1/recommendations/construct",
        headers=headers,
        json={
            "nutrient_minimums": {"iron": "1000"},
            "maximum_budget_minor": 500,
            "seed": 3,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "infeasible"
    assert body["fallback_used"] is True
    assert body["servings"]
    assert float(body["unmet_nutrient_minimums"]["iron"]) > 0
    assert "requested_constraints_infeasible" in body["warnings"]


def test_constructed_meal_rejects_unknown_nutrient_code(client: TestClient) -> None:
    headers = _student_headers(client)
    _profile(client, headers)
    response = client.post(
        "/api/v1/recommendations/construct",
        headers=headers,
        json={
            "nutrient_minimums": {"invented_nutrient": "1"},
            "maximum_budget_minor": 1000,
        },
    )
    assert response.status_code == 422
    assert "unknown nutrient codes" in response.json()["detail"]
