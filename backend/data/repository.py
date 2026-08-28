from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.data.models import Conjunction, OrbitalRecord, SpaceObject


def save_object(
    session: Session,
    object_id: str,
    name: str | None = None,
    object_type: str | None = None,
) -> SpaceObject:
    space_object = session.get(SpaceObject, object_id)

    if space_object is None:
        space_object = SpaceObject(
            object_id=object_id,
            name=name,
            object_type=object_type,
        )
        session.add(space_object)
    else:
        space_object.name = name or space_object.name
        space_object.object_type = object_type or space_object.object_type

    session.commit()
    session.refresh(space_object)
    return space_object


def save_raw_orbital_record(
    session: Session,
    object_id: str,
    epoch_utc: datetime | None,
    source: str,
    retrieved_at: datetime,
    raw_record: str,
    validation_status: str,
    tle_line1: str | None = None,
    tle_line2: str | None = None,
) -> OrbitalRecord:
    record = OrbitalRecord(
        object_id=object_id,
        epoch_utc=epoch_utc,
        source=source,
        retrieved_at=retrieved_at,
        raw_record=raw_record,
        validation_status=validation_status,
        tle_line1=tle_line1,
        tle_line2=tle_line2,
    )

    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_latest_record(
    session: Session,
    object_id: str,
) -> OrbitalRecord | None:
    query = (
        select(OrbitalRecord)
        .where(OrbitalRecord.object_id == object_id)
        .order_by(OrbitalRecord.retrieved_at.desc())
        .limit(1)
    )

    return session.scalar(query)


def get_record_history(
    session: Session,
    object_id: str,
) -> list[OrbitalRecord]:
    query = (
        select(OrbitalRecord)
        .where(OrbitalRecord.object_id == object_id)
        .order_by(OrbitalRecord.retrieved_at.desc())
    )

    return list(session.scalars(query))


def save_conjunction(
    session: Session,
    conjunction_id: str,
    object_a: str,
    object_b: str,
    tca: datetime,
    miss_distance_km: float,
    relative_velocity_km_s: float,
) -> Conjunction:
    conjunction = Conjunction(
        conjunction_id=conjunction_id,
        object_a=object_a,
        object_b=object_b,
        tca=tca,
        miss_distance_km=miss_distance_km,
        relative_velocity_km_s=relative_velocity_km_s,
    )

    session.add(conjunction)
    session.commit()
    session.refresh(conjunction)
    return conjunction