"""Idempotent local-only seed data for reproducible software demonstrations."""

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from nutritwin_api.models import (
    ChemicalSubstance,
    ConsentRecord,
    DataSource,
    Food,
    FoodNutrient,
    FoodOntologyMapping,
    Nutrient,
    QualitativeInteractionEvidence,
    Role,
    TargetRuleRecord,
    User,
)
from nutritwin_api.security import hash_password

NUTRIENTS = {
    "energy": ("Energy", "kcal"),
    "protein": ("Protein", "g"),
    "iron": ("Iron", "mg"),
    "vitamin_c": ("Vitamin C", "mg"),
}

DEMO_TARGETS = {
    "energy": ("2000", "1800", "3000"),
    "protein": ("50", "40", "150"),
    "iron": ("10", "8", "40"),
    "vitamin_c": ("60", "50", "1000"),
}

DEMO_ACCOUNTS = {
    "student@example.com": (Role.STUDENT, "StudentDemo!2026"),
    "adult@example.com": (Role.ADULT, "AdultDemo!2026"),
    "admin@example.com": (Role.ADMIN, "AdminDemo!2026"),
}


def _default_dataset_path() -> Path:
    return _resolve_data_path("demo_synthetic_foods.json")


def _default_chemistry_path() -> Path:
    return _resolve_data_path("demo_chemistry_references.json")


def _resolve_data_path(filename: str) -> Path:
    """Resolve copied repository data before considering an editable-source layout."""
    candidates = (
        Path.cwd() / "data" / "processed" / filename,
        Path(__file__).resolve().parents[4] / "data" / "processed" / filename,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    attempted = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"could not locate {filename}; attempted: {attempted}")


def seed_database(
    db: Session,
    dataset_path: Path | None = None,
    chemistry_path: Path | None = None,
) -> dict[str, int]:
    dataset = json.loads((dataset_path or _default_dataset_path()).read_text(encoding="utf-8"))
    source_spec = dataset["source"]
    source = db.scalar(select(DataSource).where(DataSource.code == source_spec["code"]))
    if source is None:
        source = DataSource(
            code=source_spec["code"],
            title=source_spec["title"],
            organization=source_spec["organization"],
            url=source_spec["url"],
            publication_date=None,
            license=source_spec["license"],
            redistribution_status=source_spec["redistribution_status"],
            checksum_sha256=None,
            authoritative=source_spec["authoritative"],
            version=source_spec["version"],
            effective_from=date.fromisoformat(source_spec["effective_from"]),
        )
        db.add(source)
        db.flush()

    nutrient_records: dict[str, Nutrient] = {}
    for code, (name, unit) in NUTRIENTS.items():
        nutrient = db.scalar(select(Nutrient).where(Nutrient.code == code))
        if nutrient is None:
            nutrient = Nutrient(code=code, name=name, canonical_unit=unit)
            db.add(nutrient)
            db.flush()
        nutrient_records[code] = nutrient

    for code, (rda, ear, tul) in DEMO_TARGETS.items():
        external_id = f"demo-adult-18-120-{code}"
        exists = db.scalar(
            select(TargetRuleRecord).where(
                TargetRuleRecord.source_id == source.id,
                TargetRuleRecord.external_rule_id == external_id,
                TargetRuleRecord.version == "1",
            )
        )
        if exists is None:
            db.add(
                TargetRuleRecord(
                    external_rule_id=external_id,
                    source_id=source.id,
                    nutrient_id=nutrient_records[code].id,
                    rda=Decimal(rda),
                    ear=Decimal(ear),
                    tul=Decimal(tul),
                    minimum_age=Decimal("18"),
                    maximum_age_exclusive=Decimal("120"),
                    source_sex_category=None,
                    activity_level=None,
                    version="1",
                    model_version="demo-target-v1",
                    effective_from=date(2026, 1, 1),
                    effective_to=None,
                    approved=True,
                )
            )

    for food_spec in dataset["foods"]:
        food = db.scalar(select(Food).where(Food.food_code == food_spec["food_code"]))
        if food is None:
            food = Food(
                food_code=food_spec["food_code"],
                name=food_spec["name"],
                source_id=source.id,
                source_food_id=food_spec["source_food_id"],
                edible_fraction=Decimal(food_spec["edible_fraction"]),
                authoritative=food_spec["authoritative"],
                dietary_tags=food_spec["dietary_tags"],
                allergens=food_spec["allergens"],
            )
            db.add(food)
            db.flush()
            for code, (amount, unit) in food_spec["nutrients"].items():
                db.add(
                    FoodNutrient(
                        food_id=food.id,
                        nutrient_id=nutrient_records[code].id,
                        amount_per_100g=Decimal(amount),
                        canonical_unit=unit,
                        value_status="synthetic_demo",
                        missing_reason=None,
                        source_version="1",
                    )
                )

    chemistry = json.loads(
        (chemistry_path or _default_chemistry_path()).read_text(encoding="utf-8")
    )
    chemistry_sources: dict[str, DataSource] = {}
    for source_spec in chemistry["sources"]:
        chemistry_source = db.scalar(
            select(DataSource).where(DataSource.code == source_spec["code"])
        )
        if chemistry_source is None:
            chemistry_source = DataSource(
                code=source_spec["code"],
                title=source_spec["title"],
                organization=source_spec["organization"],
                url=source_spec["url"],
                publication_date=None,
                license=source_spec["license"],
                redistribution_status=source_spec["redistribution_status"],
                checksum_sha256=None,
                authoritative=source_spec["authoritative"],
                version=source_spec["version"],
                effective_from=date.fromisoformat(source_spec["effective_from"]),
            )
            db.add(chemistry_source)
            db.flush()
        chemistry_sources[source_spec["code"]] = chemistry_source

    substances: dict[str, ChemicalSubstance] = {}
    for substance_spec in chemistry["substances"]:
        substance_source = chemistry_sources[substance_spec["source_code"]]
        substance = db.scalar(
            select(ChemicalSubstance).where(
                ChemicalSubstance.source_id == substance_source.id,
                ChemicalSubstance.chebi_id == substance_spec["chebi_id"],
                ChemicalSubstance.source_version == substance_spec["source_version"],
            )
        )
        if substance is None:
            substance = ChemicalSubstance(
                preferred_name=substance_spec["preferred_name"],
                synonyms=substance_spec["synonyms"],
                chebi_id=substance_spec["chebi_id"],
                molecular_formula=substance_spec["molecular_formula"],
                canonical_smiles=substance_spec["canonical_smiles"],
                inchi=substance_spec["inchi"],
                inchi_key=substance_spec["inchi_key"],
                source_id=substance_source.id,
                source_version=substance_spec["source_version"],
                review_status=substance_spec["review_status"],
                effective_from=date.fromisoformat(substance_spec["effective_from"]),
                effective_to=None,
            )
            db.add(substance)
            db.flush()
        substances[substance_spec["chebi_id"]] = substance

    for mapping_spec in chemistry["food_mappings"]:
        food = db.scalar(select(Food).where(Food.food_code == mapping_spec["food_code"]))
        if food is None:
            raise ValueError(
                f"chemistry mapping references unknown food {mapping_spec['food_code']}"
            )
        mapping_source = chemistry_sources[mapping_spec["source_code"]]
        mapping = db.scalar(
            select(FoodOntologyMapping).where(
                FoodOntologyMapping.food_id == food.id,
                FoodOntologyMapping.ontology_id == mapping_spec["ontology_id"],
                FoodOntologyMapping.source_version == mapping_spec["source_version"],
            )
        )
        if mapping is None:
            db.add(
                FoodOntologyMapping(
                    food_id=food.id,
                    source_id=mapping_source.id,
                    ontology_id=mapping_spec["ontology_id"],
                    ontology_iri=mapping_spec["ontology_iri"],
                    preferred_label=mapping_spec["preferred_label"],
                    mapping_type=mapping_spec["mapping_type"],
                    confidence=Decimal(mapping_spec["confidence"]),
                    source_version=mapping_spec["source_version"],
                    review_status=mapping_spec["review_status"],
                    effective_from=date.fromisoformat(mapping_spec["effective_from"]),
                    effective_to=None,
                )
            )

    for evidence_spec in chemistry["qualitative_evidence"]:
        substance = substances[evidence_spec["substance_chebi_id"]]
        nutrient = nutrient_records[evidence_spec["target_nutrient_code"]]
        evidence_source = chemistry_sources[evidence_spec["source_code"]]
        evidence = db.scalar(
            select(QualitativeInteractionEvidence).where(
                QualitativeInteractionEvidence.substance_id == substance.id,
                QualitativeInteractionEvidence.target_nutrient_id == nutrient.id,
                QualitativeInteractionEvidence.source_id == evidence_source.id,
                QualitativeInteractionEvidence.version == evidence_spec["version"],
            )
        )
        if evidence is None:
            db.add(
                QualitativeInteractionEvidence(
                    substance_id=substance.id,
                    target_nutrient_id=nutrient.id,
                    source_id=evidence_source.id,
                    direction=evidence_spec["direction"],
                    interaction_scope=evidence_spec["interaction_scope"],
                    timing_window=evidence_spec["timing_window"],
                    evidence_strength=evidence_spec["evidence_strength"],
                    citation_url=evidence_spec["citation_url"],
                    citation_doi=evidence_spec["citation_doi"],
                    citation_pmid=evidence_spec["citation_pmid"],
                    review_status=evidence_spec["review_status"],
                    calculation_effect=False,
                    version=evidence_spec["version"],
                    effective_from=date.fromisoformat(evidence_spec["effective_from"]),
                    effective_to=None,
                )
            )

    for email, (role, password) in DEMO_ACCOUNTS.items():
        user = db.scalar(select(User).where(User.email_normalized == email))
        if user is None:
            user = User(email_normalized=email, role=role, password_hash=hash_password(password))
            db.add(user)
            db.flush()
            db.add(
                ConsentRecord(
                    user_id=user.id,
                    document_version="demo-consent-v1",
                    purpose="core_application",
                    granted=True,
                )
            )
    db.commit()
    return {
        "sources": 1 + len(chemistry["sources"]),
        "nutrients": len(NUTRIENTS),
        "target_rules": len(DEMO_TARGETS),
        "foods": len(dataset["foods"]),
        "substances": len(chemistry["substances"]),
        "food_mappings": len(chemistry["food_mappings"]),
        "qualitative_evidence": len(chemistry["qualitative_evidence"]),
        "users": len(DEMO_ACCOUNTS),
    }
