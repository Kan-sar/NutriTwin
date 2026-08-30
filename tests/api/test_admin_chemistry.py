from datetime import date

import pytest
from fastapi.testclient import TestClient
from nutritwin_api.models import (
    ChemicalSubstance,
    DataSource,
    Nutrient,
    QualitativeInteractionEvidence,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker


def _headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_admin_can_inspect_provenance_bearing_chemistry(client: TestClient) -> None:
    student = _headers(client, "student@example.com", "StudentDemo!2026")
    assert client.get("/api/v1/admin/substances", headers=student).status_code == 403
    assert client.get("/api/v1/admin/evidence", headers=student).status_code == 403

    admin = _headers(client, "admin@example.com", "AdminDemo!2026")
    chemistry = client.get("/api/v1/admin/substances", headers=admin)
    assert chemistry.status_code == 200
    body = chemistry.json()
    assert body["model_version"] == "nutrition-chemistry-reference-v1"
    assert {row["chebi_id"] for row in body["substances"]} == {
        "CHEBI:27732",
        "CHEBI:29073",
    }
    assert {row["provenance"]["license"] for row in body["substances"]} == {"CC BY 4.0"}
    assert len(body["food_mappings"]) == 3
    assert {row["mapping_type"] for row in body["food_mappings"]} == {"exact", "broad"}

    evidence = client.get("/api/v1/admin/evidence", headers=admin)
    assert evidence.status_code == 200
    row = evidence.json()["evidence"][0]
    assert row["substance_chebi_id"] == "CHEBI:29073"
    assert row["target_nutrient_code"] == "iron"
    assert row["direction"] == "enhances"
    assert row["calculation_effect"] is False
    assert "cannot alter" in evidence.json()["notice"]


def test_database_rejects_calculation_active_qualitative_evidence(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        substance = session.scalar(
            select(ChemicalSubstance).where(ChemicalSubstance.chebi_id == "CHEBI:29073")
        )
        nutrient = session.scalar(select(Nutrient).where(Nutrient.code == "iron"))
        source = session.scalar(select(DataSource).where(DataSource.code == "NIH-ODS-IRON"))
        assert substance is not None and nutrient is not None and source is not None
        session.add(
            QualitativeInteractionEvidence(
                substance_id=substance.id,
                target_nutrient_id=nutrient.id,
                source_id=source.id,
                direction="enhances",
                interaction_scope="same_meal_context",
                timing_window=None,
                evidence_strength="test",
                citation_url="https://example.invalid/test",
                citation_doi=None,
                citation_pmid=None,
                review_status="test",
                calculation_effect=True,
                version="invalid-active-test",
                effective_from=date(2026, 8, 30),
                effective_to=None,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
