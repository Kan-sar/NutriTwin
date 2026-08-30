"""Read-only initial Admin inspection surfaces with enforced RBAC."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from nutritwin_api.database import get_db
from nutritwin_api.models import AuditEvent, DataSource, Role, TargetRuleRecord, User
from nutritwin_api.security import require_roles

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
AdminUser = Annotated[User, Depends(require_roles(Role.ADMIN))]


@router.get("/reference-data")
def reference_data(_: AdminUser, db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    sources = db.scalars(select(DataSource).order_by(DataSource.code)).all()
    rules = db.scalars(
        select(TargetRuleRecord).options(
            selectinload(TargetRuleRecord.source), selectinload(TargetRuleRecord.nutrient)
        )
    ).all()
    return {
        "sources": [
            {
                "code": source.code,
                "title": source.title,
                "version": source.version,
                "authoritative": source.authoritative,
                "redistribution_status": source.redistribution_status,
            }
            for source in sources
        ],
        "target_rules": [
            {
                "id": rule.id,
                "external_rule_id": rule.external_rule_id,
                "nutrient_code": rule.nutrient.code,
                "source_code": rule.source.code,
                "version": rule.version,
                "approved": rule.approved,
            }
            for rule in rules
        ],
        "notice": (
            "Scientific mutation/approval workflow is deferred; this endpoint is inspect-only."
        ),
    }


@router.get("/audit-events")
def audit_events(_: AdminUser, db: Annotated[Session, Depends(get_db)]) -> list[dict[str, Any]]:
    events = db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(100)).all()
    return [
        {
            "id": event.id,
            "actor_user_id": event.actor_user_id,
            "action": event.action,
            "object_type": event.object_type,
            "object_id": event.object_id,
            "created_at": event.created_at,
        }
        for event in events
    ]
