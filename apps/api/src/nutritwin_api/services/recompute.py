"""Idempotent materialization-job orchestration shared by API and Celery."""

import hashlib
import uuid
from datetime import date
from typing import Any, cast

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from nutritwin_api.models import Meal, Profile, RecomputeJob, User, utc_now
from nutritwin_api.services.targets import get_or_create_target_snapshot
from nutritwin_api.services.twin import build_twin_summary


def input_revision_for_day(db: Session, user_id: uuid.UUID, affected_date: date) -> str:
    rows = db.execute(
        select(Meal.id, Meal.revision, Meal.deleted_at)
        .where(Meal.user_id == user_id, Meal.local_date == affected_date)
        .order_by(Meal.id)
    ).all()
    payload = "|".join(
        f"{meal_id}:{revision}:{deleted_at is not None}" for meal_id, revision, deleted_at in rows
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def ensure_recompute_job(db: Session, user_id: uuid.UUID, affected_date: date) -> RecomputeJob:
    revision = input_revision_for_day(db, user_id, affected_date)
    existing = db.scalar(
        select(RecomputeJob).where(
            RecomputeJob.user_id == user_id,
            RecomputeJob.affected_date == affected_date,
            RecomputeJob.input_revision == revision,
            RecomputeJob.model_version == "twin-summary-v1",
        )
    )
    if existing is not None:
        return existing
    job = RecomputeJob(
        user_id=user_id,
        affected_date=affected_date,
        input_revision=revision,
        model_version="twin-summary-v1",
    )
    try:
        with db.begin_nested():
            db.add(job)
            db.flush()
    except IntegrityError:
        duplicate = db.scalar(
            select(RecomputeJob).where(
                RecomputeJob.user_id == user_id,
                RecomputeJob.affected_date == affected_date,
                RecomputeJob.input_revision == revision,
                RecomputeJob.model_version == "twin-summary-v1",
            )
        )
        if duplicate is None:
            raise
        return duplicate
    return job


def execute_recompute_job(db: Session, job_id: uuid.UUID) -> dict[str, Any]:
    job = db.get(RecomputeJob, job_id)
    if job is None:
        raise ValueError("recompute job not found")
    if job.status == "completed" and job.result_trace is not None:
        return dict(job.result_trace)
    user = db.get(User, job.user_id)
    profile = db.scalar(select(Profile).where(Profile.user_id == job.user_id))
    if user is None or profile is None:
        job.status = "failed"
        job.attempts += 1
        db.commit()
        raise ValueError("recompute prerequisites are unavailable")
    job.status = "running"
    job.attempts += 1
    snapshot = get_or_create_target_snapshot(db, user, profile, job.affected_date)
    result = cast(
        "dict[str, Any]",
        jsonable_encoder(build_twin_summary(db, user.id, snapshot, job.affected_date)),
    )
    job.result_trace = result
    job.status = "completed"
    job.completed_at = utc_now()
    db.commit()
    return result
