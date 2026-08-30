"""Apply the schema separately, then idempotently seed local demo records."""

from nutritwin_api.config import get_settings
from nutritwin_api.database import create_database_engine, create_session_factory
from nutritwin_api.seed import seed_database


def main() -> None:
    settings = get_settings()
    factory = create_session_factory(create_database_engine(settings.database_url))
    with factory() as session:
        counts = seed_database(session)
    print("seeded " + ", ".join(f"{key}={value}" for key, value in counts.items()))


if __name__ == "__main__":
    main()
