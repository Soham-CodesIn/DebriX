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