from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from nutritwin_api.config import Settings
from nutritwin_api.database import create_database_engine, create_session_factory
from nutritwin_api.main import create_app
from nutritwin_api.models import Base
from nutritwin_api.seed import seed_database
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture
def session_factory() -> Generator[sessionmaker[Session]]:
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    with factory() as session:
        seed_database(session)
    yield factory
    engine.dispose()


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> Generator[TestClient]:
    settings = Settings(
        environment="test",
        database_url="sqlite+pysqlite:///:memory:",
        jwt_secret="test-only-secret-that-is-at-least-32-characters",  # pragma: allowlist secret
        auto_create_schema=False,
    )
    with TestClient(create_app(settings, session_factory)) as test_client:
        yield test_client


@pytest.fixture
def registered_user(client: TestClient) -> dict[str, str]:
    payload = {
        "email": "registered.student@example.com",
        "password": "correct-horse-battery-staple",  # pragma: allowlist secret -- test fixture
        "role": "student",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    return payload


@pytest.fixture
def tokens(client: TestClient, registered_user: dict[str, str]) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
    )
    assert response.status_code == 200
    return response.json()
