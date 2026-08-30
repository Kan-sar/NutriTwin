"""add nutrition chemistry evidence foundation

Revision ID: 7d8c0f4a2b11
Revises: 3e3eeacd57ce
Create Date: 2026-08-30 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7d8c0f4a2b11"
down_revision: str | Sequence[str] | None = "3e3eeacd57ce"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chemical_substances",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("preferred_name", sa.String(length=256), nullable=False),
        sa.Column("synonyms", sa.JSON(), nullable=False),
        sa.Column("chebi_id", sa.String(length=32), nullable=False),
        sa.Column("molecular_formula", sa.String(length=128), nullable=False),
        sa.Column("canonical_smiles", sa.Text(), nullable=False),
        sa.Column("inchi", sa.Text(), nullable=False),
        sa.Column("inchi_key", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("source_version", sa.String(length=64), nullable=False),
        sa.Column("review_status", sa.String(length=64), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_id",
            "chebi_id",
            "source_version",
            name="uq_chemical_substance_source_version",
        ),
    )
    with op.batch_alter_table("chemical_substances", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_chemical_substances_chebi_id"), ["chebi_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_chemical_substances_inchi_key"), ["inchi_key"], unique=False
        )

    op.create_table(
        "food_ontology_mappings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("food_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("ontology_id", sa.String(length=64), nullable=False),
        sa.Column("ontology_iri", sa.String(length=1024), nullable=False),
        sa.Column("preferred_label", sa.String(length=256), nullable=False),
        sa.Column("mapping_type", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("source_version", sa.String(length=64), nullable=False),
        sa.Column("review_status", sa.String(length=64), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="ck_food_ontology_mapping_confidence",
        ),
        sa.ForeignKeyConstraint(["food_id"], ["foods.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "food_id",
            "ontology_id",
            "source_version",
            name="uq_food_ontology_mapping_version",
        ),
    )
    with op.batch_alter_table("food_ontology_mappings", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_food_ontology_mappings_food_id"), ["food_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_food_ontology_mappings_ontology_id"),
            ["ontology_id"],
            unique=False,
        )

    op.create_table(
        "qualitative_interaction_evidence",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("substance_id", sa.Uuid(), nullable=False),
        sa.Column("target_nutrient_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("direction", sa.String(length=32), nullable=False),
        sa.Column("interaction_scope", sa.String(length=64), nullable=False),
        sa.Column("timing_window", sa.String(length=128), nullable=True),
        sa.Column("evidence_strength", sa.String(length=64), nullable=False),
        sa.Column("citation_url", sa.String(length=1024), nullable=False),
        sa.Column("citation_doi", sa.String(length=256), nullable=True),
        sa.Column("citation_pmid", sa.String(length=32), nullable=True),
        sa.Column("review_status", sa.String(length=64), nullable=False),
        sa.Column("calculation_effect", sa.Boolean(), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "calculation_effect = false",
            name="ck_qualitative_evidence_no_calculation_effect",
        ),
        sa.ForeignKeyConstraint(["substance_id"], ["chemical_substances.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_nutrient_id"], ["nutrients.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["data_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "substance_id",
            "target_nutrient_id",
            "source_id",
            "version",
            name="uq_qualitative_interaction_evidence_version",
        ),
    )
    with op.batch_alter_table("qualitative_interaction_evidence", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_qualitative_interaction_evidence_substance_id"),
            ["substance_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("qualitative_interaction_evidence", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_qualitative_interaction_evidence_substance_id"))
    op.drop_table("qualitative_interaction_evidence")

    with op.batch_alter_table("food_ontology_mappings", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_food_ontology_mappings_ontology_id"))
        batch_op.drop_index(batch_op.f("ix_food_ontology_mappings_food_id"))
    op.drop_table("food_ontology_mappings")

    with op.batch_alter_table("chemical_substances", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_chemical_substances_inchi_key"))
        batch_op.drop_index(batch_op.f("ix_chemical_substances_chebi_id"))
    op.drop_table("chemical_substances")
