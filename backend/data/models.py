from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.data.database import Base


class SpaceObject(Base):
    __tablename__ = "objects"

    object_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    object_type: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class OrbitalRecord(Base):
    __tablename__ = "orbital_records"

    record_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    object_id: Mapped[str] = mapped_column(
        ForeignKey("objects.object_id"),
        index=True,
    )
    epoch_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    tle_line1: Mapped[str | None] = mapped_column(String, nullable=True)
    tle_line2: Mapped[str | None] = mapped_column(String, nullable=True)
    raw_record: Mapped[str] = mapped_column(Text)
    validation_status: Mapped[str] = mapped_column(String)


class Conjunction(Base):
    __tablename__ = "conjunctions"

    conjunction_id: Mapped[str] = mapped_column(String, primary_key=True)
    object_a: Mapped[str] = mapped_column(String, index=True)
    object_b: Mapped[str] = mapped_column(String, index=True)
    tca: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    miss_distance_km: Mapped[float] = mapped_column(Float)
    relative_velocity_km_s: Mapped[float] = mapped_column(Float)
class PropagationState(Base):
    __tablename__ = "propagation_states"

    state_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    object_id: Mapped[str] = mapped_column(
        ForeignKey("objects.object_id"),
        index=True,
    )
    source_record_id: Mapped[int] = mapped_column(
        ForeignKey("orbital_records.record_id"),
    )
    time_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    x_km: Mapped[float] = mapped_column(Float)
    y_km: Mapped[float] = mapped_column(Float)
    z_km: Mapped[float] = mapped_column(Float)
    vx_km_s: Mapped[float] = mapped_column(Float)
    vy_km_s: Mapped[float] = mapped_column(Float)
    vz_km_s: Mapped[float] = mapped_column(Float)
    frame: Mapped[str] = mapped_column(String)
    propagation_status: Mapped[str] = mapped_column(String)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    assessment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conjunction_id: Mapped[str] = mapped_column(
        ForeignKey("conjunctions.conjunction_id"),
        index=True,
    )
    pc: Mapped[float | None] = mapped_column(Float, nullable=True)
    pc_status: Mapped[str] = mapped_column(String)
    f_value: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String)
    confidence: Mapped[str] = mapped_column(String)
    methodology_version: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class RiskFeature(Base):
    __tablename__ = "risk_features"

    feature_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conjunction_id: Mapped[str] = mapped_column(
        ForeignKey("conjunctions.conjunction_id"),
        index=True,
    )
    feature_name: Mapped[str] = mapped_column(String)
    raw_value: Mapped[float] = mapped_column(Float)
    normalized_value: Mapped[float] = mapped_column(Float)


class Alert(Base):
    __tablename__ = "alerts"

    alert_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conjunction_id: Mapped[str] = mapped_column(
        ForeignKey("conjunctions.conjunction_id"),
        index=True,
    )
    severity: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="open")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )