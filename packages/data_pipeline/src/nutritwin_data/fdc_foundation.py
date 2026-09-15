"""Reproducible transform for a bounded USDA FDC Foundation Foods subset."""

from __future__ import annotations

import hashlib
import json
import urllib.request
import zipfile
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

SOURCE_URL = (
    "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_json_2026-04-30.zip"
)
SOURCE_FILENAME = "FoodData_Central_foundation_food_json_2026-04-30.zip"
SOURCE_MEMBER = "FoodData_Central_foundation_food_json_2026-04-30.json"
# pragma: allowlist nextline secret -- public USDA archive integrity digest
SOURCE_ARCHIVE_SHA256 = "186e988ec542e913f51ef62b86a47758e8cdd0d1dc3889e7b055581f3c09c77a"
TRANSFORM_VERSION = "fdc-foundation-subset-v2"

SELECTED_FOODS: dict[int, dict[str, Any]] = {
    746771: {"tags": ["vegetarian", "vegan"], "allergens": []},
    1999633: {"tags": ["vegetarian", "vegan"], "allergens": []},
    1999634: {"tags": ["vegetarian", "vegan"], "allergens": []},
    2259793: {"tags": ["vegetarian"], "allergens": ["milk"]},
    2512379: {"tags": ["vegetarian", "vegan"], "allergens": []},
    2644282: {"tags": ["vegetarian", "vegan"], "allergens": []},
    2644283: {"tags": ["vegetarian", "vegan"], "allergens": []},
    2644285: {"tags": ["vegetarian", "vegan"], "allergens": []},
}

# Fixed, inspected single-plant records. Source preparation descriptors remain intact.
for _food_id in (
    321360,
    323505,
    325430,
    326196,
    327046,
    327357,
    330458,
    333281,
    746764,
    746768,
    746769,
    746770,
    746773,
    747447,
    748278,
    748608,
    790577,
    790646,
    1104647,
    1104962,
    1105073,
    1105314,
    1750339,
    1750340,
    1750341,
    1750342,
    1750343,
    1999626,
    1999627,
    1999628,
    1999629,
    1999632,
    2258586,
    2258587,
    2258588,
    2258589,
    2258590,
    2258591,
    2346388,
    2346389,
    2346390,
    2346391,
    2346398,
    2346399,
    2346400,
    2346401,
    2346402,
    2346403,
    2346404,
    2346405,
    2346406,
    2346407,
    2346408,
    2346409,
    2346410,
    2346411,
    2346412,
    2346413,
    2685568,
    2685569,
    2685570,
    2685571,
    2685572,
    2685573,
    2685574,
    2685575,
):
    SELECTED_FOODS[_food_id] = {"tags": ["vegetarian", "vegan"], "allergens": []}

NUTRIENTS: dict[int, tuple[str, str]] = {
    1008: ("energy", "kcal"),
    1003: ("protein", "g"),
    1089: ("iron", "mg"),
    1162: ("vitamin_c", "mg"),
    1087: ("calcium", "mg"),
    1090: ("magnesium", "mg"),
    1092: ("potassium", "mg"),
    1093: ("sodium", "mg"),
    1095: ("zinc", "mg"),
    1079: ("fiber", "g"),
    1004: ("fat", "g"),
    1005: ("carbohydrate", "g"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def acquire_archive(destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "NutriTwin-academic-prototype/0.1"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        destination.write_bytes(response.read())
    actual = sha256_file(destination)
    if actual != SOURCE_ARCHIVE_SHA256:
        raise ValueError(f"FDC archive checksum mismatch: {actual}")
    return destination


def load_foundation_foods(archive: Path) -> list[dict[str, Any]]:
    actual = sha256_file(archive)
    if actual != SOURCE_ARCHIVE_SHA256:
        raise ValueError(f"FDC archive checksum mismatch: {actual}")
    with zipfile.ZipFile(archive) as bundle:
        if SOURCE_MEMBER not in bundle.namelist():
            raise ValueError(f"expected FDC archive member is missing: {SOURCE_MEMBER}")
        payload = json.load(bundle.open(SOURCE_MEMBER))
    foods = payload.get("FoundationFoods")
    if not isinstance(foods, list):
        raise ValueError("FDC FoundationFoods array is missing")
    return [food for food in foods if isinstance(food, dict)]


def _nutrient_rows(food: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = {
        item.get("nutrient", {}).get("id"): item
        for item in food.get("foodNutrients", [])
        if isinstance(item, dict) and item.get("nutrient", {}).get("id") in NUTRIENTS
    }
    rows: list[dict[str, Any]] = []
    for nutrient_id, (code, expected_unit) in NUTRIENTS.items():
        item = by_id.get(nutrient_id)
        if item is None or item.get("amount") is None:
            rows.append(
                {
                    "nutrient_code": code,
                    "amount_per_100g": None,
                    "unit": expected_unit,
                    "value_status": "missing",
                    "missing_reason": "not_reported",
                    "source_nutrient_id": nutrient_id,
                }
            )
            continue
        amount = item["amount"]
        actual_unit = str(item["nutrient"]["unitName"]).casefold()
        if actual_unit != expected_unit:
            raise ValueError(
                f"unexpected unit for FDC {food['fdcId']} nutrient {nutrient_id}: {actual_unit}"
            )
        rows.append(
            {
                "nutrient_code": code,
                "amount_per_100g": str(amount),
                "unit": expected_unit,
                "value_status": "reported",
                "missing_reason": None,
                "source_nutrient_id": nutrient_id,
            }
        )
    return rows


def transform(archive: Path, output: Path, manifest_path: Path) -> tuple[Path, Path]:
    foods = load_foundation_foods(archive)
    by_id = {int(food["fdcId"]): food for food in foods if food.get("fdcId") is not None}
    missing_ids = set(SELECTED_FOODS) - set(by_id)
    if missing_ids:
        raise ValueError("selected FDC identifiers missing: " + ", ".join(map(str, missing_ids)))
    transformed = []
    for fdc_id, metadata in sorted(SELECTED_FOODS.items()):
        food = by_id[fdc_id]
        transformed.append(
            {
                "food_code": f"usda-fdc-{fdc_id}",
                "name": f"USDA FDC — {food['description']}",
                "source_food_id": str(fdc_id),
                "source_description": food["description"],
                "data_type": food.get("dataType"),
                "publication_date": food.get("publicationDate"),
                "edible_fraction": "1",
                "authoritative": False,
                "dietary_tags": metadata["tags"],
                "allergens": metadata["allergens"],
                "nutrients": _nutrient_rows(food),
            }
        )
    dataset = {
        "schema_version": "1",
        "transform_version": TRANSFORM_VERSION,
        "source": {
            "code": "USDA-FDC-FOUNDATION-2026-04",
            "title": "USDA FoodData Central Foundation Foods, April 2026 subset",
            "organization": "U.S. Department of Agriculture, Agricultural Research Service",
            "url": SOURCE_URL,
            "license": "CC0-1.0",
            "redistribution_status": "permitted",
            "authoritative": False,
            "version": "Foundation Foods 2026-04-30",
            "effective_from": "2026-04-30",
            "checksum_sha256": SOURCE_ARCHIVE_SHA256,
            "limitations": (
                "USDA analytical data are a non-authoritative gap source for NutriTwin; "
                "they do not replace ICMR-NIN or IFCT for Indian requirements and foods."
            ),
        },
        "foods": transformed,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(dataset, indent=2, sort_keys=True) + "\n").encode()
    output.write_bytes(encoded)
    manifest = {
        "schema_version": "1",
        "transform_version": TRANSFORM_VERSION,
        "retrieved_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "source_url": SOURCE_URL,
        "source_filename": SOURCE_FILENAME,
        "source_sha256": SOURCE_ARCHIVE_SHA256,
        "source_license": "CC0-1.0",
        "selected_fdc_ids": sorted(SELECTED_FOODS),
        "source_food_count": len(foods),
        "processed_food_count": len(transformed),
        "processed_file": output.name,
        "processed_sha256": hashlib.sha256(encoded).hexdigest(),
        "transformations": [
            "selected fixed FDC identifiers",
            "normalized twelve nutrient identifiers and canonical units; no energy imputation",
            "represented absent nutrient amounts as missing/not_reported",
            "added inspected plant-food dietary tags and milk allergen metadata; "
            "not exhaustive allergen certification",
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return output, manifest_path


def validate(dataset_path: Path, manifest_path: Path) -> dict[str, int]:
    encoded = dataset_path.read_bytes()
    dataset = json.loads(encoded)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if hashlib.sha256(encoded).hexdigest() != manifest["processed_sha256"]:
        raise ValueError("FDC processed checksum does not match manifest")
    source = dataset["source"]
    if source["license"] != "CC0-1.0" or source["authoritative"] is not False:
        raise ValueError("FDC source must remain CC0 and non-authoritative for Indian use")
    if source["checksum_sha256"] != SOURCE_ARCHIVE_SHA256:
        raise ValueError("FDC source checksum is not the pinned release checksum")
    foods = dataset["foods"]
    if len(foods) != len(SELECTED_FOODS) or len(foods) != manifest["processed_food_count"]:
        raise ValueError("FDC processed food count mismatch")
    reported = 0
    missing = 0
    for food in foods:
        if not food["name"].startswith("USDA FDC — ") or food["authoritative"] is not False:
            raise ValueError("FDC food provenance label or authority flag is invalid")
        rows = food["nutrients"]
        if {row["nutrient_code"] for row in rows} != {value[0] for value in NUTRIENTS.values()}:
            raise ValueError(f"incomplete nutrient normalization for {food['food_code']}")
        for row in rows:
            if row["amount_per_100g"] is None:
                if row["value_status"] != "missing" or not row["missing_reason"]:
                    raise ValueError("missing FDC value lacks explicit missingness metadata")
                missing += 1
            else:
                try:
                    amount = Decimal(row["amount_per_100g"])
                except (InvalidOperation, TypeError) as exc:
                    raise ValueError("invalid FDC nutrient amount") from exc
                if amount < 0 or row["value_status"] != "reported":
                    raise ValueError("invalid reported FDC nutrient row")
                reported += 1
    return {"foods": len(foods), "reported_nutrients": reported, "missing_nutrients": missing}
