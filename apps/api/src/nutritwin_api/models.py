"""Transactional and historical relational model."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Role(StrEnum):
    STUDENT = "student"
    ADULT = "adult"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email_normalized: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False, length=16))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    family_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    document_version: Mapped[str] = mapped_column(String(64))
    purpose: Mapped[str] = mapped_column(String(64), default="core_application")
    granted: Mapped[bool] = mapped_column(Boolean)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    birth_date: Mapped[date] = mapped_column(Date)
    source_sex_category: Mapped[str | None] = mapped_column(String(32))
    activity_level: Mapped[str | None] = mapped_column(String(32))
    dietary_pattern: Mapped[str] = mapped_column(String(32), default="unrestricted")
    allergens: Mapped[list[str]] = mapped_column(JSON, default=list)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(String(512))
    organization: Mapped[str] = mapped_column(String(256))
    url: Mapped[str | None] = mapped_column(String(1024))
    publication_date: Mapped[date | None] = mapped_column(Date)
    license: Mapped[str] = mapped_column(String(256))
    redistribution_status: Mapped[str] = mapped_column(String(64))
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    authoritative: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[str] = mapped_column(String(64))
    effective_from: Mapped[date] = mapped_column(Date)


class Nutrient(Base):
    __tablename__ = "nutrients"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    canonical_unit: Mapped[str] = mapped_column(String(16))


class TargetRuleRecord(Base):
    __tablename__ = "target_rules"
    __table_args__ = (
        UniqueConstraint("source_id", "external_rule_id", "version", name="uq_target_rule_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    external_rule_id: Mapped[str] = mapped_column(String(128))
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("data_sources.id"))
    nutrient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("nutrients.id"))
    rda: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    ear: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    tul: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    minimum_age: Mapped[Decimal] = mapped_column(Numeric(8, 3))
    maximum_age_exclusive: Mapped[Decimal] = mapped_column(Numeric(8, 3))
    source_sex_category: Mapped[str | None] = mapped_column(String(32))
    activity_level: Mapped[str | None] = mapped_column(String(32))
    version: Mapped[str] = mapped_column(String(64))
    model_version: Mapped[str] = mapped_column(String(64))
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)

    source: Mapped[DataSource] = relationship()
    nutrient: Mapped[Nutrient] = relationship()


class TargetSnapshot(Base):
    __tablename__ = "target_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "profile_revision", "model_version", name="uq_target_snapshot_input"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    profile_revision: Mapped[int] = mapped_column(Integer)
    model_version: Mapped[str] = mapped_column(String(64))
    provisional: Mapped[bool] = mapped_column(Boolean)
    trace: Mapped[dict[str, Any]] = mapped_column(JSON)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    values: Mapped[list[TargetValue]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan", lazy="selectin"
    )


class TargetValue(Base):
    __tablename__ = "target_values"
    __table_args__ = (UniqueConstraint("snapshot_id", "nutrient_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("target_snapshots.id", ondelete="CASCADE")
    )
    nutrient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("nutrients.id"))
    target_rule_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("target_rules.id"))
    rda: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    ear: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    tul: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    canonical_unit: Mapped[str] = mapped_column(String(16))
    snapshot: Mapped[TargetSnapshot] = relationship(back_populates="values")
    nutrient: Mapped[Nutrient] = relationship(lazy="joined")


class Food(Base):
    __tablename__ = "foods"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    food_code: Mapped[str] = mapped_column(String(128), unique=True)
    name: Mapped[str] = mapped_column(String(256), index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("data_sources.id"))
    source_food_id: Mapped[str] = mapped_column(String(128))
    edible_fraction: Mapped[Decimal] = mapped_column(Numeric(8, 6), default=Decimal("1"))
    authoritative: Mapped[bool] = mapped_column(Boolean, default=False)
    dietary_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    allergens: Mapped[list[str]] = mapped_column(JSON, default=list)
    source: Mapped[DataSource] = relationship()
    nutrients: Mapped[list[FoodNutrient]] = relationship(
        back_populates="food", cascade="all, delete-orphan", lazy="selectin"
    )


class FoodNutrient(Base):
    __tablename__ = "food_nutrients"
    __table_args__ = (UniqueConstraint("food_id", "nutrient_id", "source_version"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    food_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("foods.id", ondelete="CASCADE"))
    nutrient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("nutrients.id"))
    amount_per_100g: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    canonical_unit: Mapped[str] = mapped_column(String(16))
    value_status: Mapped[str] = mapped_column(String(32), default="reported")
    missing_reason: Mapped[str | None] = mapped_column(String(64))
    source_version: Mapped[str] = mapped_column(String(64))
    food: Mapped[Food] = relationship(back_populates="nutrients")
    nutrient: Mapped[Nutrient] = relationship(lazy="joined")


class ChemicalSubstance(Base):
    """Versioned, provenance-bearing chemistry reference; never a clinical assertion."""

    __tablename__ = "chemical_substances"
    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "chebi_id",
            "source_version",
            name="uq_chemical_substance_source_version",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    preferred_name: Mapped[str] = mapped_column(String(256))
    synonyms: Mapped[list[str]] = mapped_column(JSON, default=list)
    chebi_id: Mapped[str] = mapped_column(String(32), index=True)
    molecular_formula: Mapped[str] = mapped_column(String(128))
    canonical_smiles: Mapped[str] = mapped_column(Text)
    inchi: Mapped[str] = mapped_column(Text)
    inchi_key: Mapped[str] = mapped_column(String(32), index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("data_sources.id"))
    source_version: Mapped[str] = mapped_column(String(64))
    review_status: Mapped[str] = mapped_column(String(64))
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    source: Mapped[DataSource] = relationship(lazy="joined")


class FoodOntologyMapping(Base):
    """Reviewed mapping from a project food to a versioned FoodOn class."""

    __tablename__ = "food_ontology_mappings"
    __table_args__ = (
        UniqueConstraint(
            "food_id",
            "ontology_id",
            "source_version",
            name="uq_food_ontology_mapping_version",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_food_ontology_mapping_confidence",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    food_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("foods.id", ondelete="CASCADE"), index=True
    )
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("data_sources.id"))
    ontology_id: Mapped[str] = mapped_column(String(64), index=True)
    ontology_iri: Mapped[str] = mapped_column(String(1024))
    preferred_label: Mapped[str] = mapped_column(String(256))
    mapping_type: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    source_version: Mapped[str] = mapped_column(String(64))
    review_status: Mapped[str] = mapped_column(String(64))
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    food: Mapped[Food] = relationship(lazy="joined")
    source: Mapped[DataSource] = relationship(lazy="joined")


class QualitativeInteractionEvidence(Base):
    """Informational nutrient-substance evidence that is forbidden from changing totals."""

    __tablename__ = "qualitative_interaction_evidence"
    __table_args__ = (
        UniqueConstraint(
            "substance_id",
            "target_nutrient_id",
            "source_id",
            "version",
            name="uq_qualitative_interaction_evidence_version",
        ),
        CheckConstraint(
            "calculation_effect = false",
            name="ck_qualitative_evidence_no_calculation_effect",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    substance_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chemical_substances.id", ondelete="CASCADE"), index=True
    )
    target_nutrient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("nutrients.id"))
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("data_sources.id"))
    direction: Mapped[str] = mapped_column(String(32))
    interaction_scope: Mapped[str] = mapped_column(String(64))
    timing_window: Mapped[str | None] = mapped_column(String(128))
    evidence_strength: Mapped[str] = mapped_column(String(64))
    citation_url: Mapped[str] = mapped_column(String(1024))
    citation_doi: Mapped[str | None] = mapped_column(String(256))
    citation_pmid: Mapped[str | None] = mapped_column(String(32))
    review_status: Mapped[str] = mapped_column(String(64))
    calculation_effect: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[str] = mapped_column(String(64))
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    substance: Mapped[ChemicalSubstance] = relationship(lazy="joined")
    target_nutrient: Mapped[Nutrient] = relationship(lazy="joined")
    source: Mapped[DataSource] = relationship(lazy="joined")


class Meal(Base):
    __tablename__ = "meals"
    __table_args__ = (Index("ix_meals_user_local_date", "user_id", "local_date"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(256))
    eaten_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    local_date: Mapped[date] = mapped_column(Date)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    ingredients: Mapped[list[MealIngredient]] = relationship(
        back_populates="meal", cascade="all, delete-orphan", lazy="selectin"
    )


class MealIngredient(Base):
    __tablename__ = "meal_ingredients"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    meal_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("meals.id", ondelete="CASCADE"))
    food_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("foods.id"))
    quantity_g: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    edible_fraction_override: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
    meal: Mapped[Meal] = relationship(back_populates="ingredients")
    food: Mapped[Food] = relationship(lazy="joined")


class RecommendationDecision(Base):
    __tablename__ = "recommendation_decisions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    local_date: Mapped[date] = mapped_column(Date)
    candidate_id: Mapped[str] = mapped_column(String(128))
    accepted: Mapped[bool] = mapped_column(Boolean)
    score: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    trace: Mapped[dict[str, Any]] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class RecomputeJob(Base):
    __tablename__ = "recompute_jobs"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "affected_date",
            "input_revision",
            "model_version",
            name="uq_recompute_job_input",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    affected_date: Mapped[date] = mapped_column(Date)
    input_revision: Mapped[str] = mapped_column(String(64))
    model_version: Mapped[str] = mapped_column(String(64), default="twin-summary-v1")
    status: Mapped[str] = mapped_column(String(32), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    result_trace: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(128))
    object_type: Mapped[str] = mapped_column(String(64))
    object_id: Mapped[str] = mapped_column(String(128))
    request_id: Mapped[str | None] = mapped_column(String(64))
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
