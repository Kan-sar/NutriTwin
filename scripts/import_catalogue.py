"""Import the verified USDA catalogue without creating demo accounts or targets."""

import argparse
from pathlib import Path

from nutritwin_api.config import get_settings
from nutritwin_api.database import create_database_engine, create_session_factory
from nutritwin_api.services.catalogue import import_fdc_catalogue


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset", type=Path, default=Path("data/processed/fdc_foundation_subset.json")
    )
    parser.add_argument(
        "--manifest", type=Path, default=Path("data/processed/fdc_foundation_subset.manifest.json")
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Persist validated catalogue rows; default is a dry run",
    )
    args = parser.parse_args()
    engine = create_database_engine(get_settings().database_url)
    try:
        with create_session_factory(engine)() as db:
            counts = import_fdc_catalogue(db, args.dataset, args.manifest)
            if args.commit:
                db.commit()
            else:
                db.rollback()
            print(("committed: " if args.commit else "dry run rolled back: ") + str(counts))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
