import uuid
from typing import Any

from nutritwin_api.config import get_settings
from nutritwin_api.database import create_database_engine, create_session_factory
from nutritwin_api.services.recompute import execute_recompute_job

from nutritwin_worker.celery_app import celery_app


@celery_app.task(name="nutritwin.recompute_job")  # type: ignore[untyped-decorator]
def recompute_job(job_id: str) -> dict[str, Any]:
    settings = get_settings()
    factory = create_session_factory(create_database_engine(settings.database_url))
    with factory() as session:
        return execute_recompute_job(session, uuid.UUID(job_id))
