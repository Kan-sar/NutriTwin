"""Pydantic request and response contracts."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from nutritwin_api.models import Role


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(ApiModel):
    error: str
    request_id: str | None = None


class UserPublic(ApiModel):
    id: uuid.UUID
    email: str
    role: Role


class RegisterRequest(ApiModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: Role

    @field_validator("role")
    @classmethod
    def no_admin_self_registration(cls, value: Role) -> Role:
        if value == Role.ADMIN:
            raise ValueError("admin accounts cannot self-register")
        return value


class LoginRequest(ApiModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(ApiModel):
    refresh_token: str = Field(min_length=32, max_length=512)


class TokenResponse(ApiModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int


class ConsentRequest(ApiModel):
    document_version: str = Field(min_length=1, max_length=64)
    purpose: str = Field(default="core_application", min_length=1, max_length=64)
    granted: bool


class ConsentResponse(ApiModel):
    id: uuid.UUID
    document_version: str
    purpose: str
    granted: bool
    recorded_at: datetime


class ProfileUpsert(ApiModel):
    birth_date: date
    source_sex_category: str | None = Field(default=None, max_length=32)
    activity_level: str | None = Field(default=None, max_length=32)
    dietary_pattern: str = Field(default="unrestricted", max_length=32)
    allergens: list[str] = Field(default_factory=list, max_length=32)

    @field_validator("allergens")
    @classmethod
    def normalize_allergens(cls, values: list[str]) -> list[str]:
        normalized = sorted({value.strip().casefold() for value in values if value.strip()})
        return normalized


class ProfileResponse(ProfileUpsert):
    id: uuid.UUID
    revision: int


class FoodNutrientResponse(ApiModel):
    nutrient_code: str
    amount_per_100g: Decimal | None
    unit: str
    value_status: str
    missing_reason: str | None


class FoodResponse(ApiModel):
    id: uuid.UUID
    food_code: str
    name: str
    source_code: str
    source_food_id: str
    authoritative: bool
    dietary_tags: list[str]
    allergens: list[str]
    nutrients: list[FoodNutrientResponse]


class MealIngredientRequest(ApiModel):
    food_id: uuid.UUID
    quantity_g: Decimal = Field(gt=0, le=5000, max_digits=10, decimal_places=3)


class MealCreate(ApiModel):
    name: str = Field(min_length=1, max_length=256)
    eaten_at: datetime
    local_date: date
    ingredients: list[MealIngredientRequest] = Field(min_length=1, max_length=50)


class MealResponse(ApiModel):
    id: uuid.UUID
    name: str
    eaten_at: datetime
    local_date: date
    revision: int
    ingredients: list[MealIngredientRequest]


class TargetValueResponse(ApiModel):
    nutrient_code: str
    rda: Decimal | None
    ear: Decimal | None
    tul: Decimal | None
    unit: str
    target_rule_id: uuid.UUID


class TargetSnapshotResponse(ApiModel):
    id: uuid.UUID
    profile_revision: int
    model_version: str
    provisional: bool
    calculated_at: datetime
    trace: dict[str, object]
    values: list[TargetValueResponse]


class SourceProvenanceResponse(ApiModel):
    code: str
    title: str
    organization: str
    url: str | None
    license: str
    version: str
    authoritative: bool


class ChemicalSubstanceResponse(ApiModel):
    id: uuid.UUID
    preferred_name: str
    synonyms: list[str]
    chebi_id: str
    molecular_formula: str
    canonical_smiles: str
    inchi: str
    inchi_key: str
    source_version: str
    review_status: str
    effective_from: date
    provenance: SourceProvenanceResponse


class FoodOntologyMappingResponse(ApiModel):
    id: uuid.UUID
    food_code: str
    food_name: str
    ontology_id: str
    ontology_iri: str
    preferred_label: str
    mapping_type: str
    confidence: Decimal
    source_version: str
    review_status: str
    effective_from: date
    provenance: SourceProvenanceResponse


class AdminChemistryResponse(ApiModel):
    model_version: str
    notice: str
    substances: list[ChemicalSubstanceResponse]
    food_mappings: list[FoodOntologyMappingResponse]


class QualitativeInteractionEvidenceResponse(ApiModel):
    id: uuid.UUID
    substance_chebi_id: str
    substance_name: str
    target_nutrient_code: str
    direction: str
    interaction_scope: str
    timing_window: str | None
    evidence_strength: str
    citation_url: str
    citation_doi: str | None
    citation_pmid: str | None
    review_status: str
    calculation_effect: bool
    version: str
    effective_from: date
    provenance: SourceProvenanceResponse


class AdminQualitativeEvidenceResponse(ApiModel):
    model_version: str
    notice: str
    evidence: list[QualitativeInteractionEvidenceResponse]
