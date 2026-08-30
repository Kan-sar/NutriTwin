from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from nutritwin_api.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def ready(db: Annotated[Session, Depends(get_db)]) -> dict[str, str | dict[str, str]]:
    db.execute(text("SELECT 1"))
    return {
        "status": "ready",
        "components": {
            "postgresql": "available",
            "redis": "optional_not_checked",
            "neo4j": "optional_not_checked",
            "llm": "disabled",
        },
    }
