import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from nutritwin_data.chemistry import validate_chemistry_dataset

DATASET = Path("data/processed/demo_chemistry_references.json")


def _data() -> dict[str, Any]:
    return json.loads(DATASET.read_text(encoding="utf-8"))


def _write(tmp_path: Path, data: dict[str, Any]) -> Path:
    path = tmp_path / "chemistry.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_chemistry_dataset_has_provenance_and_rdkit_valid_structures() -> None:
    counts = validate_chemistry_dataset(DATASET, require_rdkit=True)

    assert counts == {
        "sources": 3,
        "substances": 2,
        "food_mappings": 3,
        "qualitative_evidence": 1,
        "rdkit_used": True,
    }


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("canonical_smiles", "not-smiles", "invalid SMILES"),
        ("molecular_formula", "C1H1", "molecular formula mismatch"),
    ],
)
def test_chemistry_dataset_rejects_structure_conflicts(
    tmp_path: Path, field: str, value: str, message: str
) -> None:
    data = _data()
    data["substances"][0][field] = value

    with pytest.raises(ValueError, match=message):
        validate_chemistry_dataset(_write(tmp_path, data), require_rdkit=True)


def test_chemistry_dataset_rejects_duplicate_inchi_keys(tmp_path: Path) -> None:
    data = _data()
    duplicate = deepcopy(data["substances"][0])
    duplicate["chebi_id"] = "CHEBI:999999"
    data["substances"].append(duplicate)

    with pytest.raises(ValueError, match="share an InChIKey"):
        validate_chemistry_dataset(_write(tmp_path, data))


def test_qualitative_evidence_can_never_be_calculation_active(tmp_path: Path) -> None:
    data = _data()
    data["qualitative_evidence"][0]["calculation_effect"] = True

    with pytest.raises(ValueError, match="cannot affect calculations"):
        validate_chemistry_dataset(_write(tmp_path, data))
