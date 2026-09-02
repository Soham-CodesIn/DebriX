from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.data.models import Conjunction, OrbitalRecord, SpaceObject
from backend.data.models import PropagationState, RiskAssessment, RiskFeature, Alert

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
    conjunction = session.get(Conjunction, conjunction_id)

    if conjunction is None:
        conjunction = Conjunction(
            conjunction_id=conjunction_id,
            object_a=object_a,
            object_b=object_b,
            tca=tca,
            miss_distance_km=miss_distance_km,
            relative_velocity_km_s=relative_velocity_km_s,
        )
        session.add(conjunction)
    else:
        conjunction.object_a = object_a
        conjunction.object_b = object_b
        conjunction.tca = tca
        conjunction.miss_distance_km = miss_distance_km
        conjunction.relative_velocity_km_s = relative_velocity_km_s

    session.commit()
    session.refresh(conjunction)
    return conjunction

def save_propagation_state(session, object_id, source_record_id, time_utc,
                            x_km, y_km, z_km, vx_km_s, vy_km_s, vz_km_s,
                            frame, propagation_status):
    state = PropagationState(
        object_id=object_id,
        source_record_id=source_record_id,
        time_utc=time_utc,
        x_km=x_km, y_km=y_km, z_km=z_km,
        vx_km_s=vx_km_s, vy_km_s=vy_km_s, vz_km_s=vz_km_s,
        frame=frame,
        propagation_status=propagation_status,
    )
    session.add(state)
    session.commit()
    return state


def save_risk_assessment(session, conjunction_id, pc, pc_status, f_value,
                          risk_level, confidence, methodology_version):
    assessment = RiskAssessment(
        conjunction_id=conjunction_id,
        pc=pc,
        pc_status=pc_status,
        f_value=f_value,
        risk_level=risk_level,
        confidence=confidence,
        methodology_version=methodology_version,
    )
    session.add(assessment)
    session.commit()
    return assessment


def save_risk_feature(session, conjunction_id, feature_name, raw_value, normalized_value):
    feature = RiskFeature(
        conjunction_id=conjunction_id,
        feature_name=feature_name,
        raw_value=raw_value,
        normalized_value=normalized_value,
    )
    session.add(feature)
    session.commit()
    return feature


def save_alert(session, conjunction_id, severity, status="open"):
    alert = Alert(
        conjunction_id=conjunction_id,
        severity=severity,
        status=status,
    )
    session.add(alert)
    session.commit()
    return alert


def get_latest_propagation_state(session, object_id):
    return (
        session.query(PropagationState)
        .filter_by(object_id=object_id)
        .order_by(PropagationState.time_utc.desc())
        .first()
    )


def get_risk_assessment(session, conjunction_id):
    return (
        session.query(RiskAssessment)
        .filter_by(conjunction_id=conjunction_id)
        .order_by(RiskAssessment.created_at.desc())
        .first()
    )

def get_risk_features(session, conjunction_id):
    return session.query(RiskFeature).filter_by(conjunction_id=conjunction_id).all()


def get_open_alerts(session):
    return session.query(Alert).filter_by(status="open").all()

def get_object(session: Session, object_id: str) -> SpaceObject | None:
    return session.get(SpaceObject, object_id)


def get_all_objects(session: Session) -> list[SpaceObject]:
    return list(session.scalars(select(SpaceObject)))


def get_conjunction(session: Session, conjunction_id: str) -> Conjunction | None:
    return session.get(Conjunction, conjunction_id)


def get_all_conjunctions(session: Session) -> list[Conjunction]:
    query = select(Conjunction).order_by(Conjunction.tca.desc())
    return list(session.scalars(query))