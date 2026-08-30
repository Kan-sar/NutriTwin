from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_migration_upgrades_clean_database_and_matches_metadata(
    tmp_path: Path, monkeypatch: object
) -> None:
    database_path = tmp_path / "migration-test.db"
    database_url = f"sqlite+pysqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("NUTRITWIN_DATABASE_URL", database_url)  # type: ignore[attr-defined]
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    engine = create_engine(database_url)
    tables = set(inspect(engine).get_table_names())
    engine.dispose()
    assert {
        "users",
        "profiles",
        "foods",
        "meals",
        "target_snapshots",
        "chemical_substances",
        "food_ontology_mappings",
        "qualitative_interaction_evidence",
    } <= tables
    command.check(config)
