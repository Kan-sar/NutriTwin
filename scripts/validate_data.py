import argparse
from pathlib import Path

from nutritwin_data.chemistry import validate_chemistry_dataset
from nutritwin_data.synthetic_demo import validate_synthetic_dataset


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--require-rdkit",
        action="store_true",
        help="fail unless RDKit structure validation is available",
    )
    args = parser.parse_args()

    food_path = Path("data/processed/demo_synthetic_foods.json")
    food_counts = validate_synthetic_dataset(food_path)
    print(
        f"validated {food_path}: foods={food_counts['foods']}, "
        f"nutrient_rows={food_counts['nutrient_rows']}"
    )

    chemistry_path = Path("data/processed/demo_chemistry_references.json")
    chemistry_counts = validate_chemistry_dataset(chemistry_path, require_rdkit=args.require_rdkit)
    print(
        f"validated {chemistry_path}: substances={chemistry_counts['substances']}, "
        f"food_mappings={chemistry_counts['food_mappings']}, "
        f"qualitative_evidence={chemistry_counts['qualitative_evidence']}, "
        f"rdkit_used={str(chemistry_counts['rdkit_used']).lower()}"
    )


if __name__ == "__main__":
    main()
