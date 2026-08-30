from pathlib import Path

from nutritwin_data.synthetic_demo import validate_synthetic_dataset


def main() -> None:
    path = Path("data/processed/demo_synthetic_foods.json")
    counts = validate_synthetic_dataset(path)
    print(f"validated {path}: foods={counts['foods']}, nutrient_rows={counts['nutrient_rows']}")


if __name__ == "__main__":
    main()
