"""Read-only initial Admin inspection surfaces with enforced RBAC."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from nutritwin_api.database import get_db
from nutritwin_api.models import (
    AuditEvent,
    ChemicalSubstance,
    DataSource,
    FoodOntologyMapping,
    QualitativeInteractionEvidence,
    Role,
    TargetRuleRecord,
    User,
)
from nutritwin_api.schemas import AdminChemistryResponse, AdminQualitativeEvidenceResponse
from nutritwin_api.security import require_roles

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
AdminUser = Annotated[User, Depends(require_roles(Role.ADMIN))]


def _source_provenance(source: DataSource) -> dict[str, Any]:
    return {
        "code": source.code,
        "title": source.title,
        "organization": source.organization,
        "url": source.url,
        "license": source.license,
        "version": source.version,
        "authoritative": source.authoritative,
    }


@router.get("/reference-data")
def reference_data(_: AdminUser, db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    sources = db.scalars(select(DataSource).order_by(DataSource.code)).all()
    rules = db.scalars(
        select(TargetRuleRecord).options(
            selectinload(TargetRuleRecord.source), selectinload(TargetRuleRecord.nutrient)
        )
    ).all()
    return {
        "sources": [
            {
                "code": source.code,
                "title": source.title,
                "version": source.version,
                "authoritative": source.authoritative,
                "redistribution_status": source.redistribution_status,
            }
            for source in sources
        ],
        "target_rules": [
            {
                "id": rule.id,
                "external_rule_id": rule.external_rule_id,
                "nutrient_code": rule.nutrient.code,
                "source_code": rule.source.code,
                "version": rule.version,
                "approved": rule.approved,
            }
            for rule in rules
        ],
        "notice": (
            "Scientific mutation/approval workflow is deferred; this endpoint is inspect-only."
        ),
    }


@router.get("/substances", response_model=AdminChemistryResponse)
def substances(_: AdminUser, db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    substance_rows = db.scalars(
        select(ChemicalSubstance).order_by(ChemicalSubstance.chebi_id)
    ).all()
    mapping_rows = db.scalars(
        select(FoodOntologyMapping).order_by(FoodOntologyMapping.ontology_id)
    ).all()
    return {
        "model_version": "nutrition-chemistry-reference-v1",
        "notice": (
            "Non-clinical reference metadata only. Structures and ontology mappings do not "
            "predict absorption, disease, or treatment outcomes."
        ),
        "substances": [
            {
                "id": substance.id,
                "preferred_name": substance.preferred_name,
                "synonyms": substance.synonyms,
                "chebi_id": substance.chebi_id,
                "molecular_formula": substance.molecular_formula,
                "canonical_smiles": substance.canonical_smiles,
                "inchi": substance.inchi,
                "inchi_key": substance.inchi_key,
                "source_version": substance.source_version,
                "review_status": substance.review_status,
                "effective_from": substance.effective_from,
                "provenance": _source_provenance(substance.source),
            }
            for substance in substance_rows
        ],
        "food_mappings": [
            {
                "id": mapping.id,
                "food_code": mapping.food.food_code,
                "food_name": mapping.food.name,
                "ontology_id": mapping.ontology_id,
                "ontology_iri": mapping.ontology_iri,
                "preferred_label": mapping.preferred_label,
                "mapping_type": mapping.mapping_type,
                "confidence": mapping.confidence,
                "source_version": mapping.source_version,
                "review_status": mapping.review_status,
                "effective_from": mapping.effective_from,
                "provenance": _source_provenance(mapping.source),
            }
            for mapping in mapping_rows
        ],
    }


@router.get("/evidence", response_model=AdminQualitativeEvidenceResponse)
def qualitative_evidence(_: AdminUser, db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    rows = db.scalars(
        select(QualitativeInteractionEvidence).order_by(
            QualitativeInteractionEvidence.effective_from,
            QualitativeInteractionEvidence.id,
        )
    ).all()
    return {
        "model_version": "qualitative-interaction-evidence-v1",
        "notice": (
            "Informational evidence only. Database constraints require calculation_effect=false; "
            "these records cannot alter consumed or estimated-effective intake."
        ),
        "evidence": [
            {
                "id": evidence.id,
                "substance_chebi_id": evidence.substance.chebi_id,
                "substance_name": evidence.substance.preferred_name,
                "target_nutrient_code": evidence.target_nutrient.code,
                "direction": evidence.direction,
                "interaction_scope": evidence.interaction_scope,
                "timing_window": evidence.timing_window,
                "evidence_strength": evidence.evidence_strength,
                "citation_url": evidence.citation_url,
                "citation_doi": evidence.citation_doi,
                "citation_pmid": evidence.citation_pmid,
                "review_status": evidence.review_status,
                "calculation_effect": evidence.calculation_effect,
                "version": evidence.version,
                "effective_from": evidence.effective_from,
                "provenance": _source_provenance(evidence.source),
            }
            for evidence in rows
        ],
    }


@router.get("/audit-events")
def audit_events(_: AdminUser, db: Annotated[Session, Depends(get_db)]) -> list[dict[str, Any]]:
    events = db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(100)).all()
    return [
        {
            "id": event.id,
            "actor_user_id": event.actor_user_id,
            "action": event.action,
            "object_type": event.object_type,
            "object_id": event.object_id,
            "created_at": event.created_at,
        }
        for event in events
    ]
