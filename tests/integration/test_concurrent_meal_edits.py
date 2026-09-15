from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from threading import Barrier

from fastapi import HTTPException
from nutritwin_api.database import create_database_engine, create_session_factory
from nutritwin_api.models import Base, Meal, Role, User
from nutritwin_api.routers.core import _claim_meal_revision


def test_two_database_sessions_cannot_claim_the_same_meal_revision(tmp_path):
    engine = create_database_engine(f"sqlite+pysqlite:///{tmp_path / 'concurrent.db'}")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    try:
        with factory() as db:
            user = User(
                # pragma: allowlist nextline secret -- unused non-authenticating test record
                email_normalized="race@example.com", password_hash="unused", role=Role.ADULT
            )
            db.add(user)
            db.flush()
            meal = Meal(
                user_id=user.id,
                name="Original",
                eaten_at=datetime.now(UTC),
                local_date=date.today(),
            )
            db.add(meal)
            db.commit()
            meal_id = meal.id
        ready = Barrier(2)

        def edit(name):
            with factory() as db:
                loaded = db.get(Meal, meal_id)
                assert loaded.revision == 1
                ready.wait(timeout=10)
                try:
                    _claim_meal_revision(db, loaded, 1)
                except HTTPException as exc:
                    assert exc.status_code == 409
                    return None
                loaded.name = name
                db.commit()
                return name

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(edit, ["First tab", "Second tab"]))
        assert results.count(None) == 1
        with factory() as db:
            saved = db.get(Meal, meal_id)
            assert saved.revision == 2
            assert saved.name == next(result for result in results if result is not None)
    finally:
        engine.dispose()
