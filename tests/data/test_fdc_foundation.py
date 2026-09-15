import json
from pathlib import Path

from nutritwin_data.fdc_foundation import SOURCE_ARCHIVE_SHA256, validate


def test_committed_fdc_foundation_subset_is_provenance_bound_and_explicitly_incomplete() -> None:
    dataset_path = Path("data/processed/fdc_foundation_subset.json")
    manifest_path = Path("data/processed/fdc_foundation_subset.manifest.json")
    counts = validate(dataset_path, manifest_path)
    assert 50 <= counts["foods"] <= 100
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
