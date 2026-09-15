"""Reviewable scientific inputs. No reference value or multiplier is synthesized here."""

import hashlib
import json
from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from nutritwin_api.models import DataSource, Food, Nutrient, ScientificRevision, TargetRuleRecord


class EvidencePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_id: UUID
    nutrient_code: str = Field(min_length=1, max_length=64)
    version: str = Field(min_length=1, max_length=32)
    citation: HttpUrl
    scientific_review: str = Field(min_length=20, max_length=4000)
    acquisition_permission: str = Field(min_length=10, max_length=2000)


class TargetPayload(EvidencePayload):
    rda: Decimal = Field(gt=0, le=1000000)
    ear: Decimal | None = Field(default=None, gt=0, le=1000000)
    tul: Decimal | None = Field(default=None, gt=0, le=1000000)
    minimum_age: Decimal = Field(ge=0, le=120)
    maximum_age_exclusive: Decimal = Field(gt=0, le=121)
    source_sex_category: str | None = Field(default=None, max_length=32)
    activity_level: str | None = Field(default=None, max_length=32)

    @model_validator(mode="after")
    def bounds(self) -> "TargetPayload":
        if self.minimum_age >= self.maximum_age_exclusive:
            raise ValueError("age bounds are invalid")
        if self.ear is not None and self.ear > self.rda:
            raise ValueError("EAR exceeds RDA")
        if self.tul is not None and self.tul < self.rda:
            raise ValueError("upper limit is below RDA")
        return self


class EffectivePayload(EvidencePayload):
    trigger_food_code: str = Field(min_length=1, max_length=128)
    direction: Literal["enhance", "inhibit"]
    factor: Decimal = Field(ge=0, le=2)
    minimum_factor: Decimal = Field(ge=0, le=2)
    maximum_factor: Decimal = Field(ge=0, le=2)
    priority: int = Field(default=100, ge=0, le=1000)
    timing_minutes: int = Field(default=0, ge=0, le=120)
    applicability: str = Field(min_length=20, max_length=2000)
    target_food_codes: list[str] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def bounds(self) -> "EffectivePayload":
        if not self.minimum_factor <= self.factor <= self.maximum_factor:
            raise ValueError("factor outside approved bounds")
        if (self.direction == "enhance" and self.factor < 1) or (
            self.direction == "inhibit" and self.factor > 1
        ):
            raise ValueError("factor conflicts with direction")
        return self


def payload_digest(payload: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def validate_source(db: Session, payload: EvidencePayload) -> None:
    source = db.get(DataSource, payload.source_id)
    if source is None or source.code == "DEMO-SYNTHETIC":
        raise ValueError("a registered non-synthetic source is required")
    if not source.checksum_sha256:
        raise ValueError("source must have a recorded checksum")
    if db.scalar(select(Nutrient).where(Nutrient.code == payload.nutrient_code)) is None:
        raise ValueError("unknown nutrient code")
    if isinstance(payload, TargetPayload) and not source.authoritative:
        raise ValueError("target source must be registered as authoritative after source review")
    if isinstance(payload, EffectivePayload):
        codes = set(payload.target_food_codes) | {payload.trigger_food_code}
        if set(db.scalars(select(Food.food_code).where(Food.food_code.in_(codes)))) != codes:
            raise ValueError("all applicability and trigger foods must be registered")


def activate_target(db: Session, revision: ScientificRevision) -> None:
    payload = TargetPayload.model_validate(revision.payload)
    nutrient = db.scalar(select(Nutrient).where(Nutrient.code == payload.nutrient_code))
    assert nutrient is not None
    existing = db.scalar(
        select(TargetRuleRecord).where(
            TargetRuleRecord.source_id == payload.source_id,
            TargetRuleRecord.nutrient_id == nutrient.id,
            TargetRuleRecord.approved.is_(True),
            TargetRuleRecord.effective_to.is_(None),
            TargetRuleRecord.minimum_age < payload.maximum_age_exclusive,
            TargetRuleRecord.maximum_age_exclusive > payload.minimum_age,
            TargetRuleRecord.source_sex_category == payload.source_sex_category,
            TargetRuleRecord.activity_level == payload.activity_level,
        )
    )
    if existing is not None:
        raise ValueError("retire overlapping active target versions before activation")
    db.add(
        TargetRuleRecord(
            external_rule_id=str(revision.id),
            source_id=payload.source_id,
            nutrient_id=nutrient.id,
            rda=payload.rda,
            ear=payload.ear,
            tul=payload.tul,
            minimum_age=payload.minimum_age,
            maximum_age_exclusive=payload.maximum_age_exclusive,
            source_sex_category=payload.source_sex_category,
            activity_level=payload.activity_level,
            version=payload.version,
            model_version="reviewed-reference-v1",
            effective_from=revision.effective_from,
            approved=True,
        )
    )


def eligible_revisions(db: Session, on_date: date) -> list[ScientificRevision]:
    return list(
        db.scalars(
            select(ScientificRevision).where(
                ScientificRevision.kind == "effective",
                ScientificRevision.status.in_(["active", "retired"]),
                ScientificRevision.effective_from <= on_date,
            )
        )
    )
