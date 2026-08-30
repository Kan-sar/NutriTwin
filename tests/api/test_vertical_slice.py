from datetime import UTC, date, datetime

from fastapi.testclient import TestClient


def _login(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def _headers(tokens: dict[str, str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_complete_manual_workflow_without_optional_services_or_llm(client: TestClient) -> None:
    tokens = _login(client, "student@example.com", "StudentDemo!2026")
    headers = _headers(tokens)
    profile = client.put(
        "/api/v1/profiles/me",
        headers=headers,
        json={
            "birth_date": "2000-01-01",
            "source_sex_category": None,
            "activity_level": None,
            "dietary_pattern": "vegetarian",
            "allergens": ["milk"],
        },
    )
    assert profile.status_code == 200, profile.text

    targets = client.get("/api/v1/targets/current", headers=headers)
    assert targets.status_code == 200, targets.text
    assert targets.json()["provisional"] is True
    assert "not ICMR-NIN" in targets.json()["trace"]["source_notice"]

    foods = client.get("/api/v1/foods", params={"query": "lentils"}, headers=headers)
    assert foods.status_code == 200
    assert len(foods.json()) == 1
    assert foods.json()[0]["authoritative"] is False
    food_id = foods.json()[0]["id"]

    today = date.today().isoformat()
    meal_payload = {
        "name": "Manual lentil log",
        "eaten_at": datetime.now(UTC).isoformat(),
        "local_date": today,
        "ingredients": [{"food_id": food_id, "quantity_g": "100"}],
    }
    meal = client.post("/api/v1/meals", json=meal_payload, headers=headers)
    assert meal.status_code == 201, meal.text
    meal_id = meal.json()["id"]

    summary = client.get("/api/v1/twin/summary", params={"as_of": today}, headers=headers)
    assert summary.status_code == 200, summary.text
    body = summary.json()
    iron = next(item for item in body["nutrients"] if item["nutrient_code"] == "iron")
    assert iron["consumed"]["daily"]["total_amount"] == "3.0000"
    assert iron["estimated_effective"]["daily"]["total_amount"] == "3.0000"
    assert iron["consumed"] is not iron["estimated_effective"]
    warnings = iron["estimated_effective"]["calculation_trace"][0]["warnings"]
    assert "identity_estimate_no_approved_rules" in warnings
    assert "intake-gap risk indication" in iron["risk"]["wording"]
    assert body["unlogged_days_30"] == 29

    recommendations = client.get(
        "/api/v1/recommendations", params={"as_of": today}, headers=headers
    )
    assert recommendations.status_code == 200, recommendations.text
    rec_body = recommendations.json()
    assert rec_body["llm_used"] is False
    assert rec_body["recommendations"]
    assert all(
        "milk" not in item["candidate_name"].casefold() for item in rec_body["recommendations"]
    )
    yogurt = next(
        item
        for item in rec_body["rejected_candidates"]
        if item["candidate_id"] == "demo-yogurt-orange-bowl"
    )
    assert yogurt["rejection_reasons"] == ["allergens"]

    meal_payload["ingredients"][0]["quantity_g"] = "200"
    updated = client.put(f"/api/v1/meals/{meal_id}", json=meal_payload, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["revision"] == 2
    changed = client.get("/api/v1/twin/summary", params={"as_of": today}, headers=headers)
    changed_iron = next(
        item for item in changed.json()["nutrients"] if item["nutrient_code"] == "iron"
    )
    assert changed_iron["consumed"]["daily"]["total_amount"] == "6.0000"

    assert client.delete(f"/api/v1/meals/{meal_id}", headers=headers).status_code == 204
    after_delete = client.get("/api/v1/twin/summary", params={"as_of": today}, headers=headers)
    assert after_delete.json()["logged_days_30"] == 0


def test_admin_reference_inspection_is_backend_rbac_protected(client: TestClient) -> None:
    student = _headers(_login(client, "student@example.com", "StudentDemo!2026"))
    assert client.get("/api/v1/admin/reference-data", headers=student).status_code == 403
    admin = _headers(_login(client, "admin@example.com", "AdminDemo!2026"))
    response = client.get("/api/v1/admin/reference-data", headers=admin)
    assert response.status_code == 200
    sources = {source["code"]: source for source in response.json()["sources"]}
    assert sources["DEMO-SYNTHETIC"]["authoritative"] is False
