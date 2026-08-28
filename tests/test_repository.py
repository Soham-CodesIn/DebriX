from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import backend.data.models
from backend.data.database import Base
from backend.data.repository import (
    get_latest_record,
    get_record_history,
    save_object,
    save_raw_orbital_record,
)


def test_save_and_read_orbital_record():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    save_object(
        session=session,
        object_id="25544",
        name="ISS",
        object_type="PAYLOAD",
    )

    saved_record = save_raw_orbital_record(
        session=session,
        object_id="25544",
        epoch_utc=datetime(2026, 8, 29, tzinfo=timezone.utc),
        source="test",
        retrieved_at=datetime(2026, 8, 29, 12, tzinfo=timezone.utc),
        raw_record='{"NORAD_CAT_ID": "25544"}',
        validation_status="valid",
    )

    latest_record = get_latest_record(session, "25544")
    history = get_record_history(session, "25544")

    assert latest_record is not None
    assert latest_record.record_id == saved_record.record_id
    assert len(history) == 1
    assert history[0].object_id == "25544"

    session.close()