from pathlib import Path

import pytest
from nutritwin_api.seed import _resolve_data_path


def test_seed_data_resolves_from_container_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    expected = data_dir / "demo.json"
    expected.write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert _resolve_data_path("demo.json") == expected


def test_seed_data_missing_error_lists_attempted_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(FileNotFoundError, match=r"could not locate missing\.json"):
        _resolve_data_path("missing.json")
