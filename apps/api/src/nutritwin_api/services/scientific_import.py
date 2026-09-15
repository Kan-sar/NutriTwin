"""Local scientific acquisition handoff. Import never approves or activates a rule."""

import hashlib
import json
from datetime import date
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from sqlalchemy import select
from sqlalchemy.orm import Session

from nutritwin_api.models import AuditEvent, DataSource, Nutrient, Role, ScientificRevision, User
from nutritwin_api.routers.science import Proposal
from nutritwin_api.services.science import (
    EffectivePayload,
    TargetPayload,
    payload_digest,
    validate_source,
)


class SourceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=512)
    organization: str = Field(min_length=1, max_length=256)
    url: HttpUrl
    license: str = Field(min_length=1, max_length=256)
    redistribution_status: str = Field(min_length=1, max_length=64)
    version: str = Field(min_length=1, max_length=64)
    effective_from: date
    authoritative: bool = False
    checksum_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ImportManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_file: str
    acquisition_permission: str = Field(min_length=20, max_length=2000)
    source_review_record: str = Field(min_length=20, max_length=4000)
    source: SourceManifest
    canonical_units: dict[str, str]
    proposals: list[Proposal] = Field(min_length=1, max_length=1000)


def import_scientific_manifest(db: Session, manifest_path: Path, admin_id: UUID) -> list[UUID]:
    """Caller chooses commit/rollback. Source and submissions form one atomic transaction."""
    admin = db.get(User, admin_id)
    if admin is None or not admin.is_active or admin.role != Role.ADMIN:
        raise ValueError("an active Admin must perform the local acquisition handoff")
    manifest = ImportManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    acquired = Path(manifest.source_file)
    if not acquired.is_absolute():
        acquired = manifest_path.parent / acquired
    digest = hashlib.sha256(acquired.read_bytes()).hexdigest()
    if digest != manifest.source.checksum_sha256:
        raise ValueError("acquired source checksum does not match manifest")
    data = manifest.source.model_dump(mode="python")
    data["url"] = str(manifest.source.url)
    if manifest.source.authoritative and not manifest.source.code.startswith("ICMR-NIN-2020"):
        raise ValueError("only reviewed ICMR-NIN 2020 source handoffs may be authoritative")
    source = db.scalar(select(DataSource).where(DataSource.code == manifest.source.code))
    if source is not None:
        if any(getattr(source, key) != value for key, value in data.items()):
            raise ValueError("source versions are immutable; use a new source code/version")
    else:
        source = DataSource(**data)
        db.add(source)
        db.flush()
    output = []
    for proposal in manifest.proposals:
        if proposal.effective_from < date.today():
            raise ValueError("new scientific versions cannot be backdated")
        payload = dict(proposal.payload)
        payload["source_id"] = str(source.id)
        payload["acquisition_permission"] = manifest.acquisition_permission
        parsed = (TargetPayload if proposal.kind == "target" else EffectivePayload).model_validate(
            payload
        )
        nutrient = db.scalar(select(Nutrient).where(Nutrient.code == parsed.nutrient_code))
        if (
            nutrient is None
            or manifest.canonical_units.get(parsed.nutrient_code) != nutrient.canonical_unit
        ):
            raise ValueError("explicit canonical unit must match the nutrient registry")
        validate_source(db, parsed)
        normalized = parsed.model_dump(mode="json")
        checksum = payload_digest(normalized)
        existing = db.scalar(
            select(ScientificRevision).where(
                ScientificRevision.payload_sha256 == checksum,
                ScientificRevision.kind == proposal.kind,
                ScientificRevision.effective_from == proposal.effective_from,
            )
        )
        if existing is not None:
            output.append(existing.id)
            continue
        revision = ScientificRevision(
            kind=proposal.kind,
            proposer_id=admin_id,
            payload=normalized,
            payload_sha256=checksum,
            effective_from=proposal.effective_from,
        )
        db.add(revision)
        db.flush()
        db.add(
            AuditEvent(
                actor_user_id=admin_id,
                action="science.local_import",
                object_type="scientific_revision",
                object_id=str(revision.id),
                details=json.dumps(
                    {
                        "source_checksum": digest,
                        "source_review_record": manifest.source_review_record,
                    }
                ),
            )
        )
        output.append(revision.id)
    db.flush()
    return output
