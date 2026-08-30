from fastapi.testclient import TestClient


def test_health_and_openapi_are_usable(client: TestClient) -> None:
    assert client.get("/health/live").json() == {"status": "ok"}
    readiness = client.get("/health/ready")
    assert readiness.status_code == 200
    assert readiness.json()["components"]["database"] == "sqlite"
    assert readiness.json()["components"]["postgresql"] == ("development_fallback_not_postgresql")
    assert "/api/v1/auth/login" in client.get("/openapi.json").json()["paths"]


def test_registration_rejects_admin_and_duplicate_email(client: TestClient) -> None:
    admin = client.post(
        "/api/v1/auth/register",
        json={
            "email": "a@example.com",
            # pragma: allowlist nextline secret
            "password": "long-enough-password",
            "role": "admin",
        },
    )
    assert admin.status_code == 422
    payload = {
        "email": "registered.adult@example.com",
        # pragma: allowlist nextline secret
        "password": "long-enough-password",
        "role": "adult",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_access_and_refresh_rotation(
    client: TestClient, registered_user: dict[str, str], tokens: dict[str, str]
) -> None:
    me = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["role"] == "student"

    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != tokens["refresh_token"]
    reused = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert reused.status_code == 401
    family_revoked = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": rotated.json()["refresh_token"]}
    )
    assert family_revoked.status_code == 401


def test_consent_requires_authentication(client: TestClient, tokens: dict[str, str]) -> None:
    payload = {"document_version": "consent-v1", "granted": True}
    assert client.post("/api/v1/consents", json=payload).status_code == 401
    response = client.post(
        "/api/v1/consents",
        json=payload,
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert response.status_code == 201
    assert response.json()["granted"] is True
