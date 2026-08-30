import uuid

from fastapi.testclient import TestClient
from nutritwin_api.models import DataSource, TargetSnapshot
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker


def _headers(client: TestClient) -> dict[str, str]:
    token = client.post(
        "/api/v1/auth/login",
        json={
            "email": "adult@example.com",
            # pragma: allowlist nextline secret
            "password": "AdultDemo!2026",
        },
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_profile_or_reference_change_creates_new_immutable_snapshot(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    headers = _headers(client)
    profile = {
        "birth_date": "1990-01-01",
        "dietary_pattern": "unrestricted",
        "activity_level": None,
    }
    assert client.put("/api/v1/profiles/me", headers=headers, json=profile).status_code == 200
    first = client.get("/api/v1/targets/current", headers=headers).json()

    profile["activity_level"] = "moderate"
    assert client.put("/api/v1/profiles/me", headers=headers, json=profile).status_code == 200
    second = client.get("/api/v1/targets/current", headers=headers).json()
    assert first["id"] != second["id"]
    assert first["values"] == second["values"]

    with session_factory() as db:
        source = db.scalar(select(DataSource).where(DataSource.code == "DEMO-SYNTHETIC"))
        assert source is not None
        source.version = "2"
        db.commit()
    third = client.get("/api/v1/targets/current", headers=headers).json()
    assert third["id"] != second["id"]
    assert third["model_version"] != second["model_version"]

    with session_factory() as db:
        count = db.scalar(select(func.count()).select_from(TargetSnapshot))
        assert count == 3
        old = db.get(TargetSnapshot, uuid.UUID(first["id"]))
        assert old is not None and len(old.values) == 4
