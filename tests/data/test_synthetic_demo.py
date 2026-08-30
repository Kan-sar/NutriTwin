from pathlib import Path

from nutritwin_data.synthetic_demo import validate_synthetic_dataset


def test_bundled_demo_data_is_conspicuously_synthetic_and_valid() -> None:
    counts = validate_synthetic_dataset(Path("data/processed/demo_synthetic_foods.json"))
    assert counts == {"foods": 7, "nutrient_rows": 28}
