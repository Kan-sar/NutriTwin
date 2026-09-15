from datetime import date

import pytest
from nutritwin_api.models import ConsentRecord, Profile, RecomputeJob, User
from nutritwin_api.services.recompute import ensure_recompute_job
from nutritwin_worker import tasks
from sqlalchemy import select


def test_worker_failure_is_retryable_and_withdrawal_cancels_pending(session_factory, monkeypatch):
    with session_factory() as db:
        user = db.scalar(select(User).where(User.email_normalized == "student@example.com"))
        db.add(Profile(user_id=user.id, birth_date=date(2000, 1, 1)))
        db.commit()
        job = ensure_recompute_job(db, user.id, date.today())
        job_id = job.id
        db.commit()
        real = tasks.execute_recompute_job

        def unavailable(*args):
            raise RuntimeError("simulated transient service failure")

        monkeypatch.setattr(tasks, "execute_recompute_job", unavailable)
        with pytest.raises(RuntimeError):
            tasks.run_job(db, job_id)
        assert db.get(RecomputeJob, job_id).status == "failed"
        assert db.get(RecomputeJob, job_id).attempts == 1
        monkeypatch.setattr(tasks, "execute_recompute_job", real)
        result = tasks.run_job(db, job_id)
        assert result["model_version"] == "twin-summary-v2"
        assert db.get(RecomputeJob, job_id).attempts == 2
        assert tasks.run_job(db, job_id) == result
        assert db.get(RecomputeJob, job_id).attempts == 2
        other = ensure_recompute_job(db, user.id, date(2026, 1, 2))
        db.add(ConsentRecord(user_id=user.id, document_version="test", granted=False))
        db.commit()
        assert tasks.run_job(db, other.id) == {"status": "cancelled"}
        assert db.get(RecomputeJob, other.id).status == "cancelled"
