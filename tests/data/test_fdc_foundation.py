import hashlib
import json
from pathlib import Path

import pytest
from nutritwin_data.fdc_foundation import SELECTED_FOODS, SOURCE_ARCHIVE_SHA256, validate


def test_committed_fdc_foundation_subset_is_provenance_bound_and_explicitly_incomplete() -> None:
    dataset_path = Path("data/processed/fdc_foundation_subset.json")
    manifest_path = Path("data/processed/fdc_foundation_subset.manifest.json")
    counts = validate(dataset_path, manifest_path)
    assert counts["foods"] == len(SELECTED_FOODS) == 122
    assert counts["reported_nutrients"] + counts["missing_nutrients"] == counts["foods"] * 12
    assert counts["missing_nutrients"] > 0

    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert dataset["source"]["checksum_sha256"] == SOURCE_ARCHIVE_SHA256
    assert manifest["source_sha256"] == SOURCE_ARCHIVE_SHA256
    assert dataset["source"]["authoritative"] is False
    assert dataset["source"]["license"] == "CC0-1.0"
    assert all(food["name"].startswith("USDA FDC — ") for food in dataset["foods"])
    assert any(
        row["amount_per_100g"] is None and row["missing_reason"] == "not_reported"
        for food in dataset["foods"]
        for row in food["nutrients"]
    )


@pytest.mark.parametrize(
    "corruption", ["unit", "duplicate_food", "duplicate_nutrient", "nonfinite", "allergen"]
)
def test_catalogue_rejects_invalid_observations_even_with_updated_output_digest(
    tmp_path: Path, corruption: str
) -> None:
    dataset = json.loads(Path("data/processed/fdc_foundation_subset.json").read_text())
    manifest = json.loads(Path("data/processed/fdc_foundation_subset.manifest.json").read_text())
    food = dataset["foods"][0]
    if corruption == "unit":
        food["nutrients"][0]["unit"] = "mg"
    elif corruption == "duplicate_food":
        dataset["foods"][1] = food
    elif corruption == "duplicate_nutrient":
        food["nutrients"].append(food["nutrients"][0])
    elif corruption == "nonfinite":
        row = next(row for row in food["nutrients"] if row["amount_per_100g"] is not None)
        row["amount_per_100g"] = "NaN"
    else:
        food["allergens"] = ["unreviewed"]
    encoded = json.dumps(dataset).encode()
    manifest["processed_sha256"] = hashlib.sha256(encoded).hexdigest()
    path, meta = tmp_path / "data.json", tmp_path / "manifest.json"
    path.write_bytes(encoded)
    meta.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        validate(path, meta)
