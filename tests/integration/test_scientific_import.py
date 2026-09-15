import hashlib
import json
from datetime import date

import pytest
from nutritwin_api.models import DataSource, ScientificRevision, User
from nutritwin_api.services.scientific_import import import_scientific_manifest
from sqlalchemy import func, select


def test_local_import_is_atomic_idempotent_and_never_active(session_factory, tmp_path):
    raw = tmp_path / "fictional.txt"
    raw.write_text("Fictional source for isolated software test only.")
    source = {
        "code": "ICMR-NIN-2020-TEST-ONLY",
        "title": "Fictional source",
        "organization": "Test fixture",
        "url": "https://example.org/fictional",
        "license": "test fixture",
        "redistribution_status": "local-only",
        "version": "test-v1",
        "effective_from": date.today().isoformat(),
        "authoritative": True,
        "checksum_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
    }
    manifest = {
        "source_file": raw.name,
        "source": source,
        "canonical_units": {"iron": "mg"},
        "acquisition_permission": "Fictional local test permission only.",
        "source_review_record": "Test-only source review; not real scientific evidence.",
        "proposals": [
            {
                "kind": "target",
                "effective_from": date.today().isoformat(),
                "payload": {
                    "nutrient_code": "iron",
                    "version": "test-v1",
                    "citation": "https://example.org/test",
                    "scientific_review": "Fictional reference values for software tests only.",
                    "rda": "9",
                    "ear": "7",
                    "tul": "40",
                    "minimum_age": "18",
                    "maximum_age_exclusive": "100",
                },
            }
        ],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    with session_factory() as db:
        admin = db.scalar(select(User).where(User.email_normalized == "admin@example.com"))
        aid = admin.id
        ids = import_scientific_manifest(db, path, aid)
        assert db.get(ScientificRevision, ids[0]).status == "submitted"
        db.rollback()
        assert db.scalar(select(DataSource).where(DataSource.code == source["code"])) is None
        ids = import_scientific_manifest(db, path, aid)
        db.commit()
        assert import_scientific_manifest(db, path, aid) == ids
        assert db.scalar(select(func.count()).select_from(ScientificRevision)) == 1
        db.rollback()
        manifest["canonical_units"]["iron"] = "g"
        path.write_text(json.dumps(manifest))
        with pytest.raises(ValueError, match="canonical unit"):
            import_scientific_manifest(db, path, aid)
        db.rollback()
        manifest["canonical_units"]["iron"] = "mg"
        source["checksum_sha256"] = "0" * 64
        path.write_text(json.dumps(manifest))
        with pytest.raises(ValueError, match="checksum"):
            import_scientific_manifest(db, path, aid)
