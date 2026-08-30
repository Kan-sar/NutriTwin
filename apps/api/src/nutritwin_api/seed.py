"""Idempotent local-only seed data for reproducible software demonstrations."""

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from nutritwin_api.models import (
    ConsentRecord,
    DataSource,
    Food,
    FoodNutrient,
    Nutrient,
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
    return Path(__file__).resolve().parents[4] / "data" / "processed" / "demo_synthetic_foods.json"


def seed_database(db: Session, dataset_path: Path | None = None) -> dict[str, int]:
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
        "sources": 1,
        "nutrients": len(NUTRIENTS),
        "target_rules": len(DEMO_TARGETS),
        "foods": len(dataset["foods"]),
        "users": len(DEMO_ACCOUNTS),
    }
