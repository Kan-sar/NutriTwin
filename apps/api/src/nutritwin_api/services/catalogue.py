"""Validated food-only ingestion; never creates accounts or scientific targets."""

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from nutritwin_data.fdc_foundation import validate
from sqlalchemy import select
from sqlalchemy.orm import Session

from nutritwin_api.models import DataSource, Food, FoodNutrient, Nutrient


def import_fdc_catalogue(db: Session, dataset_path: Path, manifest_path: Path) -> dict[str, int]:
    """Caller owns commit/rollback. Existing source observations are immutable."""
    counts = validate(dataset_path, manifest_path)
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    spec = dataset["source"]
    source_data = {
        key: spec[key]
        for key in (
            "code",
            "title",
            "organization",
            "url",
            "license",
            "redistribution_status",
            "checksum_sha256",
            "authoritative",
            "version",
        )
    }
    source_data["effective_from"] = date.fromisoformat(spec["effective_from"])
    source_data["publication_date"] = date(2026, 4, 30)
    source = db.scalar(select(DataSource).where(DataSource.code == spec["code"]))
    if source is None:
        source = DataSource(**source_data)
        db.add(source)
        db.flush()
    elif any(getattr(source, key) != value for key, value in source_data.items()):
        raise ValueError(
            "existing source differs; historical source versions cannot be overwritten"
        )

    nutrients = {n.code: n for n in db.scalars(select(Nutrient))}
    foods = {f.food_code: f for f in db.scalars(select(Food))}
    inserted = 0
    for item in dataset["foods"]:
        food_data = {
            key: item[key]
            for key in (
                "food_code",
                "name",
                "source_food_id",
                "authoritative",
                "dietary_tags",
                "allergens",
            )
        }
        food_data["source_id"] = source.id
        food_data["edible_fraction"] = Decimal(item["edible_fraction"])
        food = foods.get(item["food_code"])
        if food is None:
            food = Food(**food_data)
            db.add(food)
            db.flush()
            inserted += 1
        elif any(getattr(food, key) != value for key, value in food_data.items()):
            raise ValueError(f"existing food differs: {food.food_code}; use a new version")
        for row in item["nutrients"]:
            code = row["nutrient_code"]
            nutrient = nutrients.get(code)
            if nutrient is None:
                nutrient = Nutrient(
                    code=code, name=code.replace("_", " ").title(), canonical_unit=row["unit"]
                )
                db.add(nutrient)
                db.flush()
                nutrients[code] = nutrient
            elif nutrient.canonical_unit != row["unit"]:
                raise ValueError(f"canonical unit mismatch for {code}")
            observation = {
                "amount_per_100g": None
                if row["amount_per_100g"] is None
                else Decimal(row["amount_per_100g"]),
                "canonical_unit": row["unit"],
                "value_status": row["value_status"],
                "missing_reason": row["missing_reason"],
            }
            existing = db.scalar(
                select(FoodNutrient).where(
                    FoodNutrient.food_id == food.id,
                    FoodNutrient.nutrient_id == nutrient.id,
                    FoodNutrient.source_version == source.version,
                )
            )
            if existing is None:
                db.add(
                    FoodNutrient(
                        food_id=food.id,
                        nutrient_id=nutrient.id,
                        source_version=source.version,
                        **observation,
                    )
                )
            elif any(getattr(existing, key) != value for key, value in observation.items()):
                raise ValueError(f"existing observation differs: {food.food_code}/{code}")
    db.flush()
    return {**counts, "inserted_foods": inserted}
