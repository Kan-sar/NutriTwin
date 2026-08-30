"""Acquire a small fixed CC0 USDA FoodData Central demo dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

FDC_API = "https://api.nal.usda.gov/fdc/v1/food/{fdc_id}"
TRANSFORM_VERSION = "fdc-demo-v1"
FOODS = {
    172421: {"food_code": "fdc-lentils-cooked", "name": "Lentils, cooked without salt"},
    168463: {"food_code": "fdc-spinach-cooked", "name": "Spinach, cooked without salt"},
    170457: {"food_code": "fdc-tomato-raw", "name": "Tomato, red, ripe, raw"},
    173757: {"food_code": "fdc-chickpeas-cooked", "name": "Chickpeas, cooked without salt"},
    169704: {"food_code": "fdc-brown-rice-cooked", "name": "Brown long-grain rice, cooked"},
    2259793: {"food_code": "fdc-yogurt-plain", "name": "Yogurt, plain, whole milk"},
    746771: {"food_code": "fdc-orange-raw", "name": "Orange, raw, navel"},
}
NUTRIENTS = {
    1008: ("energy", "kcal"),
    1003: ("protein", "g"),
    1089: ("iron", "mg"),
    1162: ("vitamin_c", "mg"),
}


def _fetch(fdc_id: int, api_key: str) -> tuple[dict[str, Any], str]:
    query = urllib.parse.urlencode({"api_key": api_key})
    request = urllib.request.Request(  # noqa: S310 -- constant HTTPS origin
        f"{FDC_API.format(fdc_id=fdc_id)}?{query}",
        headers={"User-Agent": "NutriTwin-academic-prototype/0.1"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
        raw = response.read()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def transform_food(raw: dict[str, Any], expected: dict[str, str]) -> dict[str, Any]:
    by_id = {
        item["nutrient"]["id"]: item
        for item in raw.get("foodNutrients", [])
        if item.get("nutrient", {}).get("id") in NUTRIENTS
    }
    nutrients: list[dict[str, Any]] = []
    for fdc_nutrient_id, (code, expected_unit) in NUTRIENTS.items():
        item = by_id.get(fdc_nutrient_id)
        if item is None or item.get("amount") is None:
            nutrients.append(
                {
                    "nutrient_code": code,
                    "amount_per_100g": None,
                    "unit": expected_unit,
                    "value_status": "missing",
                    "missing_reason": "not_reported",
                    "fdc_nutrient_id": fdc_nutrient_id,
                }
            )
            continue
        actual_unit = item["nutrient"]["unitName"].lower()
        if actual_unit != expected_unit:
            raise ValueError(
                f"unexpected FDC unit for {code}: {actual_unit}, expected {expected_unit}"
            )
        nutrients.append(
            {
                "nutrient_code": code,
                "amount_per_100g": str(item["amount"]),
                "unit": expected_unit,
                "value_status": "reported",
                "missing_reason": None,
                "fdc_nutrient_id": fdc_nutrient_id,
            }
        )
    return {
        **expected,
        "source_food_id": str(raw["fdcId"]),
        "source_description": raw["description"],
        "data_type": raw.get("dataType"),
        "publication_date": raw.get("publicationDate"),
        "edible_fraction": "1",
        "authoritative": False,
        "dietary_tags": ["vegetarian"],
        "allergens": ["milk"] if "yogurt" in expected["food_code"] else [],
        "nutrients": nutrients,
    }


def acquire(output_dir: Path, api_key: str) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    checksums: dict[str, str] = {}
    foods: list[dict[str, Any]] = []
    for fdc_id, expected in sorted(FOODS.items()):
        raw, checksum = _fetch(fdc_id, api_key)
        if raw.get("fdcId") != fdc_id:
            raise ValueError(f"FDC identity mismatch for {fdc_id}")
        checksums[str(fdc_id)] = checksum
        foods.append(transform_food(raw, expected))
    dataset = {
        "schema_version": "1",
        "transform_version": TRANSFORM_VERSION,
        "source": {
            "code": "USDA-FDC-DEMO",
            "title": "USDA FoodData Central fixed demo subset",
            "organization": "U.S. Department of Agriculture, Agricultural Research Service",
            "url": "https://fdc.nal.usda.gov/api-guide/",
            "license": "CC0-1.0",
            "redistribution_status": "permitted",
            "authoritative": False,
            "version": "API records retrieved 2026-08-30",
            "effective_from": "2026-08-30",
        },
        "foods": foods,
    }
    dataset_bytes = (json.dumps(dataset, indent=2, sort_keys=True) + "\n").encode()
    dataset_path = output_dir / "demo_foods.json"
    dataset_path.write_bytes(dataset_bytes)
    manifest = {
        "schema_version": "1",
        "transform_version": TRANSFORM_VERSION,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "source_url_template": FDC_API,
        "source_license": "CC0-1.0",
        "raw_response_sha256_by_fdc_id": checksums,
        "record_count": len(foods),
        "processed_file": dataset_path.name,
        "processed_sha256": hashlib.sha256(dataset_bytes).hexdigest(),
        "limitations": [
            "USDA records are demo/gap data and are not authoritative for Indian targets or foods.",
            (
                "Preparation, cultivar, and regional composition differences remain visible in "
                "source descriptions."
            ),
        ],
    }
    manifest_path = output_dir / "demo_foods.manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return dataset_path, manifest_path


def validate(dataset_path: Path, manifest_path: Path) -> None:
    dataset_bytes = dataset_path.read_bytes()
    dataset = json.loads(dataset_bytes)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if hashlib.sha256(dataset_bytes).hexdigest() != manifest["processed_sha256"]:
        raise ValueError("processed dataset checksum does not match manifest")
    if len(dataset["foods"]) != manifest["record_count"]:
        raise ValueError("record count does not match manifest")
    codes = [food["food_code"] for food in dataset["foods"]]
    if len(codes) != len(set(codes)):
        raise ValueError("duplicate food_code")
    for food in dataset["foods"]:
        nutrient_codes = [item["nutrient_code"] for item in food["nutrients"]]
        if set(nutrient_codes) != {item[0] for item in NUTRIENTS.values()}:
            raise ValueError(f"incomplete normalized nutrient rows for {food['food_code']}")
        for nutrient in food["nutrients"]:
            if nutrient["amount_per_100g"] is None and nutrient["missing_reason"] is None:
                raise ValueError("missing amount without missing_reason")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    dataset = args.output_dir / "demo_foods.json"
    manifest = args.output_dir / "demo_foods.manifest.json"
    if not args.validate_only:
        dataset, manifest = acquire(args.output_dir, os.getenv("FDC_API_KEY", "DEMO_KEY"))
    validate(dataset, manifest)
    print(f"validated {dataset} against {manifest}")


if __name__ == "__main__":
    main()
