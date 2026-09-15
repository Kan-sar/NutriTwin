from datetime import UTC, date, datetime
from uuid import UUID

import pytest
from nutritwin_api.models import AuditEvent, Meal, RecomputeJob
from sqlalchemy import func, select


def login(client, email, password):
    result = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert result.status_code == 200
    return {"Authorization": f"Bearer {result.json()['access_token']}"}


@pytest.mark.parametrize("stale_operation", ["PUT", "DELETE"])
def test_stale_changes_preserve_meal_audit_and_outbox(client, session_factory, stale_operation):
    headers = login(client, "student@example.com", "StudentDemo!2026")
    food = client.get("/api/v1/foods?query=lentils", headers=headers).json()[0]
    payload = {
        "name": "Original meal",
        "eaten_at": datetime.now(UTC).isoformat(),
        "local_date": date.today().isoformat(),
        "ingredients": [{"food_id": food["id"], "quantity_g": "100"}],
    }
    created = client.post("/api/v1/meals", headers=headers, json=payload).json()
    path = f"/api/v1/meals/{created['id']}"
    newer = {**payload, "name": "Saved in another tab"}
    newer["ingredients"] = [{"food_id": food["id"], "quantity_g": "250"}]
    saved = client.put(path, params={"expected_revision": 1}, headers=headers, json=newer)
    assert saved.status_code == 200
    assert saved.json()["revision"] == 2

    def counts():
        with session_factory() as db:
            return tuple(
                db.scalar(select(func.count()).select_from(m)) for m in (AuditEvent, RecomputeJob)
            )

    before = counts()
    stale = client.request(
        stale_operation,
        path,
        params={"expected_revision": 1},
        headers=headers,
        json=payload if stale_operation == "PUT" else None,
    )
    assert stale.status_code == 409
    assert "changed since you loaded" in stale.json()["detail"]
    assert counts() == before
    meals = client.get("/api/v1/meals", headers=headers).json()
    assert meals == [saved.json()]
    assert client.request(stale_operation, path, headers=headers, json=payload).status_code == 422
    assert counts() == before

    outsider = login(client, "adult@example.com", "AdultDemo!2026")
    assert client.delete(path, params={"expected_revision": 2}, headers=outsider).status_code == 404
    assert client.delete(path, params={"expected_revision": 2}, headers=headers).status_code == 204
    assert client.get("/api/v1/meals", headers=headers).json() == []
    assert (
        client.put(path, params={"expected_revision": 2}, headers=headers, json=payload).status_code
        == 404
    )
    with session_factory() as db:
        meal = db.get(Meal, UUID(created["id"]))
        assert meal.revision == 3
        assert meal.deleted_at is not None
