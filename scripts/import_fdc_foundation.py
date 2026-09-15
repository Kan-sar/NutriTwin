"""Acquire, transform, and validate the pinned USDA FDC Foundation Foods subset."""

import argparse
from pathlib import Path

from nutritwin_data.fdc_foundation import acquire_archive, transform, validate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true")
    parser.add_argument(
        "--archive",
        type=Path,
        default=Path("data/raw/FoodData_Central_foundation_food_json_2026-04-30.zip"),
    )
    parser.add_argument(
        "--output", type=Path, default=Path("data/processed/fdc_foundation_subset.json")
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/processed/fdc_foundation_subset.manifest.json"),
    )
    args = parser.parse_args()
    if args.download:
        acquire_archive(args.archive)
    transform(args.archive, args.output, args.manifest)
    counts = validate(args.output, args.manifest)
    print(
        f"validated {args.output}: foods={counts['foods']}, "
        f"reported_nutrients={counts['reported_nutrients']}, "
        f"missing_nutrients={counts['missing_nutrients']}"
    )


if __name__ == "__main__":
    main()
