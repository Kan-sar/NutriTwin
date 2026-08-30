"""Validation for the small attributed, non-clinical chemistry reference subset."""

from __future__ import annotations

import importlib
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

CHEBI_ID = re.compile(r"^CHEBI:[1-9][0-9]*$")
FOODON_ID = re.compile(r"^FOODON:[0-9]{8}$")
INCHI_KEY = re.compile(r"^[A-Z]{14}-[A-Z]{10}-[A-Z]$")


class ChemistryDependencyUnavailable(RuntimeError):
    """Raised when strict structure validation is requested without RDKit."""


def _rdkit_modules() -> tuple[Any, Any, Any] | None:
    try:
        chemistry = importlib.import_module("rdkit.Chem")
        descriptors = importlib.import_module("rdkit.Chem.rdMolDescriptors")
        inchi = importlib.import_module("rdkit.Chem.inchi")
    except ImportError:
        return None
    return chemistry, descriptors, inchi


def _require_text(record: dict[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"chemistry record requires non-empty {key}")
    return value


def _validate_substance_structure(substance: dict[str, Any], modules: tuple[Any, Any, Any]) -> None:
    chemistry, descriptors, inchi = modules
    smiles = _require_text(substance, "canonical_smiles")
    molecule = chemistry.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError(f"invalid SMILES for {substance['chebi_id']}")
    canonical = chemistry.MolToSmiles(molecule, canonical=True, isomericSmiles=True)
    if canonical != smiles:
        raise ValueError(f"non-canonical SMILES for {substance['chebi_id']}: expected {canonical}")
    formula = descriptors.CalcMolFormula(molecule)
    if formula != substance["molecular_formula"]:
        raise ValueError(f"molecular formula mismatch for {substance['chebi_id']}")
    calculated_inchi = inchi.MolToInchi(molecule)
    if calculated_inchi != substance["inchi"]:
        raise ValueError(f"InChI mismatch for {substance['chebi_id']}")
    calculated_key = inchi.MolToInchiKey(molecule)
    if calculated_key != substance["inchi_key"]:
        raise ValueError(f"InChIKey mismatch for {substance['chebi_id']}")


def validate_chemistry_dataset(path: Path, *, require_rdkit: bool = False) -> dict[str, int | bool]:
    """Validate provenance, identifiers, invariants, and optionally molecular structures."""

    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    limitations = _require_text(data, "limitations").casefold()
    if "not a clinical knowledge base" not in limitations:
        raise ValueError("chemistry dataset must state its non-clinical limitation")

    sources: list[dict[str, Any]] = data["sources"]
    source_codes = [_require_text(source, "code") for source in sources]
    if len(source_codes) != len(set(source_codes)):
        raise ValueError("chemistry source codes must be unique")
    for source in sources:
        _require_text(source, "organization")
        _require_text(source, "url")
        _require_text(source, "license")
        _require_text(source, "version")

    modules = _rdkit_modules()
    if require_rdkit and modules is None:
        raise ChemistryDependencyUnavailable(
            "RDKit is required for strict chemistry validation; install the 'chem' extra"
        )

    substances: list[dict[str, Any]] = data["substances"]
    chebi_ids: list[str] = []
    inchi_keys: list[str] = []
    for substance in substances:
        chebi_id = _require_text(substance, "chebi_id")
        inchi_key = _require_text(substance, "inchi_key")
        if CHEBI_ID.fullmatch(chebi_id) is None:
            raise ValueError(f"invalid ChEBI identifier: {chebi_id}")
        if INCHI_KEY.fullmatch(inchi_key) is None:
            raise ValueError(f"invalid InChIKey: {inchi_key}")
        if substance["source_code"] not in source_codes:
            raise ValueError(f"unknown source for {chebi_id}")
        _require_text(substance, "preferred_name")
        _require_text(substance, "molecular_formula")
        _require_text(substance, "inchi")
        _require_text(substance, "review_status")
        chebi_ids.append(chebi_id)
        inchi_keys.append(inchi_key)
        if modules is not None:
            _validate_substance_structure(substance, modules)
    if len(chebi_ids) != len(set(chebi_ids)):
        raise ValueError("ChEBI identifiers must be unique in the demonstration subset")
    if len(inchi_keys) != len(set(inchi_keys)):
        raise ValueError("conflicting substances cannot share an InChIKey")

    mappings: list[dict[str, Any]] = data["food_mappings"]
    mapping_keys: list[tuple[str, str, str]] = []
    for mapping in mappings:
        ontology_id = _require_text(mapping, "ontology_id")
        if FOODON_ID.fullmatch(ontology_id) is None:
            raise ValueError(f"invalid FoodOn identifier: {ontology_id}")
        if mapping["source_code"] not in source_codes:
            raise ValueError(f"unknown ontology source for {ontology_id}")
        if mapping["mapping_type"] not in {"exact", "close", "broad"}:
            raise ValueError(f"invalid mapping type for {ontology_id}")
        try:
            confidence = Decimal(mapping["confidence"])
        except (InvalidOperation, TypeError) as exc:
            raise ValueError(f"invalid confidence for {ontology_id}") from exc
        if not Decimal("0") <= confidence <= Decimal("1"):
            raise ValueError(f"confidence out of range for {ontology_id}")
        mapping_keys.append((mapping["food_code"], ontology_id, mapping["source_version"]))
    if len(mapping_keys) != len(set(mapping_keys)):
        raise ValueError("food ontology mappings must be unique by food, term, and version")

    evidence_rows: list[dict[str, Any]] = data["qualitative_evidence"]
    evidence_keys: list[tuple[str, str, str, str]] = []
    for evidence in evidence_rows:
        if evidence.get("calculation_effect") is not False:
            raise ValueError("qualitative evidence cannot affect calculations")
        if evidence["substance_chebi_id"] not in chebi_ids:
            raise ValueError("qualitative evidence references an unknown substance")
        if evidence["source_code"] not in source_codes:
            raise ValueError("qualitative evidence references an unknown source")
        if evidence["direction"] not in {"enhances", "inhibits", "contextual"}:
            raise ValueError("invalid qualitative evidence direction")
        _require_text(evidence, "citation_url")
        _require_text(evidence, "review_status")
        evidence_keys.append(
            (
                evidence["substance_chebi_id"],
                evidence["target_nutrient_code"],
                evidence["source_code"],
                evidence["version"],
            )
        )
    if len(evidence_keys) != len(set(evidence_keys)):
        raise ValueError("qualitative evidence versions must be unique")

    return {
        "sources": len(sources),
        "substances": len(substances),
        "food_mappings": len(mappings),
        "qualitative_evidence": len(evidence_rows),
        "rdkit_used": modules is not None,
    }
