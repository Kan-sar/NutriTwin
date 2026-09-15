"""Drain the PostgreSQL outbox; broker outages cannot lose saved meal changes."""

import logging
import uuid
from datetime import date
from typing import Any

from nutritwin_api.config import get_settings
from nutritwin_api.database import create_database_engine, create_session_factory
from nutritwin_api.models import ConsentRecord, Profile, RecomputeJob, User
from nutritwin_api.services.recompute import ensure_recompute_job, execute_recompute_job
from sqlalchemy import select
from sqlalchemy.orm import Session

from nutritwin_worker.celery_app import celery_app

logger = logging.getLogger(__name__)


def eligible(db: Session, user_id: uuid.UUID) -> bool:
    user = db.get(User, user_id)
    consent = db.scalar(
        select(ConsentRecord)
        .where(ConsentRecord.user_id == user_id, ConsentRecord.purpose == "core_application")
        .order_by(ConsentRecord.recorded_at.desc())
        .limit(1)
    )
    return user is not None and user.is_active and consent is not None and consent.granted


def run_job(db: Session, job_id: uuid.UUID) -> dict[str, Any]:
    job = db.get(RecomputeJob, job_id)
    if job is None:
        raise ValueError("recompute job not found")
    if not eligible(db, job.user_id):
        # Preserve completed historical traces; cancel unprocessed work after withdrawal.
        if job.status != "completed":
            job.status = "cancelled"
            db.commit()
        return {"status": "cancelled"}
    attempts = job.attempts
    try:
        return execute_recompute_job(db, job_id)
    except Exception:
        db.rollback()
        failed = db.get(RecomputeJob, job_id)
        if failed is not None and failed.status != "completed":
            failed.status = "failed"
            failed.attempts = max(failed.attempts, attempts + 1)
            db.commit()
        raise


@celery_app.task(name="nutritwin.recompute_job")  # type: ignore[untyped-decorator]
def recompute_job(job_id: str) -> dict[str, Any]:
    engine = create_database_engine(get_settings().database_url)
    try:
        with create_session_factory(engine)() as db:
            return run_job(db, uuid.UUID(job_id))
    finally:
        engine.dispose()


@celery_app.task(name="nutritwin.drain_pending")  # type: ignore[untyped-decorator]
def drain_pending() -> int:
    engine = create_database_engine(get_settings().database_url)
    factory = create_session_factory(engine)
    count = 0
    try:
        with factory() as db:
            jobs = list(
                db.scalars(
                    select(RecomputeJob.id)
                    .where(
                        RecomputeJob.status.in_(["pending", "failed"]), RecomputeJob.attempts < 3
                    )
                    .order_by(RecomputeJob.created_at)
                    .limit(50)
                )
            )
        for job_id in jobs:
            try:
                with factory() as db:
                    run_job(db, job_id)
                    count += 1
            except Exception:
                # One failed job must not starve the rest of the durable queue.
                logger.warning(
                    "Nutrition recomputation failed; bounded retry retained for job %s", job_id
                )
    finally:
        engine.dispose()
    return count


@celery_app.task(name="nutritwin.refresh_daily")  # type: ignore[untyped-decorator]
def refresh_daily() -> int:
    engine = create_database_engine(get_settings().database_url)
    try:
        with create_session_factory(engine)() as db:
            users = list(db.scalars(select(Profile.user_id)))
            count = 0
            for user_id in users:
                if eligible(db, user_id):
                    ensure_recompute_job(db, user_id, date.today())
                    count += 1
            db.commit()
            return count
    finally:
        engine.dispose()
