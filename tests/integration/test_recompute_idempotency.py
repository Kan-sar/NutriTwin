from datetime import date

from fastapi.testclient import TestClient
from nutritwin_api.models import Profile, RecomputeJob, User
from nutritwin_api.services.recompute import ensure_recompute_job, execute_recompute_job
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker


def test_repeated_recompute_execution_reuses_one_completed_result(
    client: TestClient, session_factory: sessionmaker[Session]
) -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "student@example.com",
            # pragma: allowlist nextline secret
            "password": "StudentDemo!2026",
        },
    ).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}
    response = client.put(
        "/api/v1/profiles/me",
        headers=headers,
        json={"birth_date": "2000-01-01", "dietary_pattern": "vegetarian"},
    )
    assert response.status_code == 200
    with session_factory() as db:
        user = db.scalar(select(User).where(User.email_normalized == "student@example.com"))
        assert user is not None
        assert db.scalar(select(Profile).where(Profile.user_id == user.id)) is not None
        job = ensure_recompute_job(db, user.id, date.today())
        db.commit()
        first = execute_recompute_job(db, job.id)
        second = execute_recompute_job(db, job.id)
        assert first == second
        jobs = db.scalars(select(RecomputeJob).where(RecomputeJob.user_id == user.id)).all()
        assert len(jobs) == 1
        assert jobs[0].attempts == 1
        assert jobs[0].status == "completed"
