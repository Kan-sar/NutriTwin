"""Validate an ignored local manifest; --commit submits it for separate Admin review."""

import argparse
from pathlib import Path
from uuid import UUID

from nutritwin_api.config import get_settings
from nutritwin_api.database import create_database_engine, create_session_factory
from nutritwin_api.services.scientific_import import import_scientific_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--admin-id", type=UUID, required=True)
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Submit immutable revisions; never approve or activate",
    )
    args = parser.parse_args()
    engine = create_database_engine(get_settings().database_url)
    try:
        with create_session_factory(engine)() as db:
            identifiers = import_scientific_manifest(db, args.manifest, args.admin_id)
            if args.commit:
                db.commit()
            else:
                db.rollback()
            print(
                f"{len(identifiers)} scientific submissions validated; "
                + ("committed for separate review" if args.commit else "dry run rolled back")
            )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
