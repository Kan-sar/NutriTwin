from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from nutritwin_api.database import create_database_engine, create_session_factory
from nutritwin_api.models import Base, Food, FoodNutrient, TargetRuleRecord, User
from nutritwin_api.services.catalogue import import_fdc_catalogue
from sqlalchemy import func, select

DATASET = Path("data/processed/fdc_foundation_subset.json")
MANIFEST = Path("data/processed/fdc_foundation_subset.manifest.json")


def test_real_catalogue_import_is_idempotent_and_does_not_create_demo_accounts_or_targets() -> None:
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with create_session_factory(engine)() as db:
        first = import_fdc_catalogue(db, DATASET, MANIFEST)
        db.commit()
        identifiers = set(db.scalars(select(Food.id)))
        second = import_fdc_catalogue(db, DATASET, MANIFEST)
        db.commit()
        assert first["inserted_foods"] == 122
        assert second["inserted_foods"] == 0
        assert set(db.scalars(select(Food.id))) == identifiers
        assert db.scalar(select(func.count(User.id))) == 0
        assert db.scalar(select(func.count(TargetRuleRecord.id))) == 0
        assert db.scalar(select(func.count(FoodNutrient.id))) == 1464
        observed = db.scalar(select(FoodNutrient).where(FoodNutrient.amount_per_100g.is_not(None)))
        assert observed is not None
        observed.amount_per_100g = Decimal("9999")
        db.commit()
        with pytest.raises(ValueError, match="existing observation differs"):
            import_fdc_catalogue(db, DATASET, MANIFEST)
        db.rollback()
    engine.dispose()


def test_source_filters_pagination_and_provenance(client: TestClient) -> None:
    token = client.post(
        "/api/v1/auth/login", json={"email": "student@example.com", "password": "StudentDemo!2026"}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    first = client.get("/api/v1/foods?source_kind=real&limit=100", headers=headers)
    second = client.get("/api/v1/foods?source_kind=real&limit=100&offset=100", headers=headers)
    assert first.status_code == second.status_code == 200
    rows = first.json() + second.json()
    assert len(rows) == len({row["id"] for row in rows}) == 122
    assert all(row["source_code"].startswith("USDA-FDC") for row in rows)
    assert any(row["food_code"] == "usda-fdc-2512380" and "raw" in row["name"] for row in rows)
    demo = client.get("/api/v1/foods?source_kind=demo", headers=headers).json()
    assert len(demo) == 7
    assert all(row["source_code"] == "DEMO-SYNTHETIC" for row in demo)
    sources = client.get("/api/v1/food-sources", headers=headers).json()
    fdc = next(row for row in sources if row["code"].startswith("USDA-FDC"))
    assert fdc["food_count"] == 122 and fdc["missing_nutrient_rows"] == 241
    assert fdc["license"] == "CC0-1.0" and fdc["synthetic"] is False
    assert client.get("/api/v1/food-sources").status_code == 401
    assert client.get("/api/v1/foods?source_kind=bogus", headers=headers).status_code == 422
