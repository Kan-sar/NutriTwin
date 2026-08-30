"""Validation for the conspicuously synthetic bundled software-demo dataset."""

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


def validate_synthetic_dataset(path: Path) -> dict[str, int]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    source = data["source"]
    if source["code"] != "DEMO-SYNTHETIC" or source["authoritative"] is not False:
        raise ValueError("bundled demo data must be non-authoritative and synthetic")
    if "not ICMR" not in source["limitations"]:
        raise ValueError("synthetic dataset must carry an explicit authority limitation")
    foods = data["foods"]
    codes = [food["food_code"] for food in foods]
    if len(codes) != len(set(codes)):
        raise ValueError("food codes must be unique")
    nutrient_rows = 0
    for food in foods:
        if not food["name"].startswith("DEMO —") or food["authoritative"] is not False:
            raise ValueError("every synthetic food must be visibly labeled and non-authoritative")
        edible = Decimal(food["edible_fraction"])
        if not Decimal("0") <= edible <= Decimal("1"):
            raise ValueError("edible fraction out of range")
        for code, value in food["nutrients"].items():
            try:
                amount = Decimal(value[0])
            except (InvalidOperation, TypeError) as exc:
                raise ValueError(f"invalid amount for {food['food_code']}:{code}") from exc
            if amount < 0:
                raise ValueError("synthetic nutrient amount cannot be negative")
            nutrient_rows += 1
    return {"foods": len(foods), "nutrient_rows": nutrient_rows}
