"""Scientific governance with two distinct Admin identities and immutable payloads."""

from datetime import date
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from nutritwin_api.database import get_db
from nutritwin_api.models import AuditEvent, ScientificRevision, TargetRuleRecord
from nutritwin_api.routers.admin import AdminUser
from nutritwin_api.services.science import (
    EffectivePayload,
    TargetPayload,
    activate_target,
    payload_digest,
    validate_source,
)

router = APIRouter(prefix="/api/v1/admin/science", tags=["scientific review"])


class Proposal(BaseModel):
    kind: Literal["target", "effective"]
    effective_from: date
    payload: dict[str, Any]


class ReviewAction(BaseModel):
    action: Literal["approve", "reject", "activate", "retire"]
    review_record: str = Field(min_length=20, max_length=4000)


def public(row: ScientificRevision) -> dict[str, Any]:
    return {
        "id": row.id,
        "kind": row.kind,
        "status": row.status,
        "payload": row.payload,
        "payload_sha256": row.payload_sha256,
        "proposer_id": row.proposer_id,
        "approver_id": row.approver_id,
        "effective_from": row.effective_from,
        "retired_on": row.retired_on,
        "review_record": row.review_record,
    }


@router.get("/revisions")
def revisions(_: AdminUser, db: Annotated[Session, Depends(get_db)]) -> list[dict[str, Any]]:
    return [
        public(row)
        for row in db.scalars(
            select(ScientificRevision).order_by(ScientificRevision.created_at.desc()).limit(100)
        )
    ]


@router.post("/revisions", status_code=201)
def propose(
    payload: Proposal, user: AdminUser, db: Annotated[Session, Depends(get_db)]
) -> dict[str, Any]:
    if payload.effective_from < date.today():
        raise HTTPException(422, "new scientific versions cannot be backdated")
    try:
        parsed = (TargetPayload if payload.kind == "target" else EffectivePayload).model_validate(
            payload.payload
        )
        validate_source(db, parsed)
    except (ValueError, ValidationError) as exc:
        raise HTTPException(422, str(exc)) from exc
    data = parsed.model_dump(mode="json")
    row = ScientificRevision(
        kind=payload.kind,
        proposer_id=user.id,
        payload=data,
        payload_sha256=payload_digest(data),
        effective_from=payload.effective_from,
    )
    db.add(row)
    db.flush()
    db.add(
        AuditEvent(
            actor_user_id=user.id,
            action="science.submitted",
            object_type="scientific_revision",
            object_id=str(row.id),
            details=row.payload_sha256,
        )
    )
    db.commit()
    return public(row)


@router.post("/revisions/{revision_id}/review")
def review(
    revision_id: UUID,
    payload: ReviewAction,
    user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    row = db.scalar(
        select(ScientificRevision).where(ScientificRevision.id == revision_id).with_for_update()
    )
    if row is None:
        raise HTTPException(404, "scientific revision not found")
    if payload_digest(row.payload) != row.payload_sha256:
        raise HTTPException(409, "scientific payload checksum mismatch")
    allowed = {
        "approve": "submitted",
        "reject": "submitted",
        "activate": "approved",
        "retire": "active",
    }
    if row.status != allowed[payload.action]:
        raise HTTPException(409, "invalid review transition")
    if payload.action in {"approve", "reject", "retire"} and user.id == row.proposer_id:
        raise HTTPException(403, "a different Admin must review this change")
    if payload.action in {"approve", "reject"}:
        row.approver_id = user.id
        row.status = "approved" if payload.action == "approve" else "rejected"
    elif payload.action == "activate":
        if date.today() > row.effective_from:
            raise HTTPException(409, "effective date has passed; submit a new version")
        try:
            parsed = (TargetPayload if row.kind == "target" else EffectivePayload).model_validate(
                row.payload
            )
            validate_source(db, parsed)
            if row.kind == "target":
                activate_target(db, row)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        row.status = "active"
    else:
        row.status = "retired"
        row.retired_on = date.today()
        target = db.scalar(
            select(TargetRuleRecord).where(TargetRuleRecord.external_rule_id == str(row.id))
        )
        if target is not None:
            target.effective_to = row.retired_on
    row.review_record = payload.review_record
    db.add(
        AuditEvent(
            actor_user_id=user.id,
            action=f"science.{payload.action}",
            object_type="scientific_revision",
            object_id=str(row.id),
            details=payload.review_record,
        )
    )
    db.commit()
    return public(row)
