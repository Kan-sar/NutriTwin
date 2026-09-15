"""Profile-dependent immutable target snapshots."""

import hashlib
from dataclasses import asdict
from datetime import date
from decimal import Decimal
from typing import Any

from nutritwin_domain.targets import ProfileFacts, TargetRule, select_targets
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from nutritwin_api.models import (
    Profile,
    ProfileVersion,
    TargetRuleRecord,
    TargetSnapshot,
    TargetValue,
    User,
)

MODEL_VERSION = "targets-v2"


def age_in_years(birth_date: date, on_date: date) -> Decimal:
    if birth_date > on_date:
        raise ValueError("birth date cannot be in the future")
    years = on_date.year - birth_date.year
    if (on_date.month, on_date.day) < (birth_date.month, birth_date.day):
        years -= 1
    return Decimal(years)


def historical_profile(db: Session, profile: Profile, on_date: date) -> tuple[int, dict[str, Any]]:
    version = db.scalar(
        select(ProfileVersion)
        .where(
            ProfileVersion.user_id == profile.user_id,
            ProfileVersion.effective_from <= on_date,
        )
        .order_by(ProfileVersion.effective_from.desc(), ProfileVersion.revision.desc())
        .limit(1)
    )
    if version is not None:
        return version.revision, version.facts
    return profile.revision, {
        "birth_date": profile.birth_date.isoformat(),
        "source_sex_category": profile.source_sex_category,
        "activity_level": profile.activity_level,
    }


def get_or_create_target_snapshot(
    db: Session, user: User, profile: Profile, on_date: date
) -> TargetSnapshot:
    # Serialize snapshot creation for one profile on PostgreSQL.
    db.execute(select(Profile.id).where(Profile.id == profile.id).with_for_update())
    revision, facts = historical_profile(db, profile, on_date)
    records = db.scalars(
        select(TargetRuleRecord).options(
            selectinload(TargetRuleRecord.source), selectinload(TargetRuleRecord.nutrient)
        )
    ).all()
    reference_fingerprint = hashlib.sha256(
        "|".join(
            sorted(
                (
                    f"{item.id}:{item.version}:{item.source.version}:{item.approved}:"
                    f"{item.effective_from}:{item.effective_to}:{item.rda}:{item.ear}:{item.tul}:"
                    f"{item.minimum_age}:{item.maximum_age_exclusive}:"
                    f"{item.source_sex_category}:{item.activity_level}"
                )
                for item in records
            )
        ).encode()
    ).hexdigest()[:12]
    snapshot_model_version = f"{MODEL_VERSION}+{reference_fingerprint}+{on_date.isoformat()}"
    existing = db.scalar(
        select(TargetSnapshot)
        .where(
            TargetSnapshot.user_id == user.id,
            TargetSnapshot.profile_revision == revision,
            TargetSnapshot.model_version == snapshot_model_version,
        )
        .options(selectinload(TargetSnapshot.values))
    )
    if existing is not None:
        return existing
    record_by_id = {str(item.id): item for item in records}
    rules = [
        TargetRule(
            id=str(item.id),
            nutrient_code=item.nutrient.code,
            canonical_unit=item.nutrient.canonical_unit,
            rda=item.rda,
            ear=item.ear,
            tul=item.tul,
            minimum_age=item.minimum_age,
            maximum_age_exclusive=item.maximum_age_exclusive,
            source_sex_category=item.source_sex_category,
            activity_level=item.activity_level,
            source_code=item.source.code,
            source_version=item.source.version,
            model_version=item.model_version,
            effective_from=item.effective_from,
            effective_to=item.effective_to,
            approved=item.approved,
            authoritative=item.source.authoritative,
        )
        for item in records
    ]
    result = select_targets(
        ProfileFacts(
            age_in_years(date.fromisoformat(facts["birth_date"]), on_date),
            facts.get("source_sex_category"),
            facts.get("activity_level"),
        ),
        rules,
        on_date,
        model_version=snapshot_model_version,
    )
    snapshot = TargetSnapshot(
        user_id=user.id,
        profile_revision=revision,
        model_version=result.model_version,
        provisional=result.provisional,
        trace={
            "as_of_date": on_date.isoformat(),
            "source_notice": (
                "Demo targets are synthetic and are not ICMR-NIN values."
                if result.provisional
                else "Reviewed authoritative reference records."
            ),
            "profile_history_notice": (
                "Initial profile facts are user-provided baseline assumptions; "
                "later revisions apply prospectively."
            ),
            "selections": [asdict(item) for item in result.trace],
        },
    )
    db.add(snapshot)
    db.flush()
    for rule in result.targets.values():
        record = record_by_id[rule.id]
        snapshot.values.append(
            TargetValue(
                nutrient_id=record.nutrient_id,
                target_rule_id=record.id,
                rda=record.rda,
                ear=record.ear,
                tul=record.tul,
                canonical_unit=record.nutrient.canonical_unit,
            )
        )
    db.flush()
    return snapshot
