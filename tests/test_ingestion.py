from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import backend.data.models  # noqa: F401  ensures models are registered on Base
from backend.data.database import Base
from backend.data.models import OrbitalRecord, SpaceObject
from backend.services.ingestion import ingest_from_spacetrack
from backend.services.spacetrack import SpaceTrackFetchResult

LINE1 = "1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753"
LINE2 = "2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667"


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_ingest_saves_valid_record():
    session = _make_session()

    fake_result = SpaceTrackFetchResult(
        success=True, status="ok",
        raw_records=[{
            "NORAD_CAT_ID": "00005",
            "OBJECT_NAME": "VANGUARD 1",
            "OBJECT_TYPE": "PAYLOAD",
            "TLE_LINE1": LINE1,
            "TLE_LINE2": LINE2,
        }],
    )

    with patch("backend.services.ingestion.fetch_gp_data", return_value=fake_result):
        result = ingest_from_spacetrack(session, "user", "pass", norad_ids=["00005"])

    assert result.success is True
    assert result.total_records == 1
    assert result.saved_valid == 1
    assert result.saved_invalid == 0

    saved_object = session.get(SpaceObject, "00005")
    assert saved_object is not None
    assert saved_object.name == "VANGUARD 1"

    records = list(session.scalars(select(OrbitalRecord).where(OrbitalRecord.object_id == "00005")))
    assert len(records) == 1
    assert records[0].validation_status == "valid"
    assert records[0].tle_line1 == LINE1


def test_ingest_saves_invalid_tle_without_dropping_it():
    session = _make_session()

    fake_result = SpaceTrackFetchResult(
        success=True, status="ok",
        raw_records=[{
            "NORAD_CAT_ID": "99999",
            "OBJECT_NAME": "BAD OBJECT",
            "OBJECT_TYPE": "DEBRIS",
            "TLE_LINE1": "garbage line",
            "TLE_LINE2": "garbage line",
        }],
    )

    with patch("backend.services.ingestion.fetch_gp_data", return_value=fake_result):
        result = ingest_from_spacetrack(session, "user", "pass")

    assert result.saved_valid == 0
    assert result.saved_invalid == 1

    records = list(session.scalars(select(OrbitalRecord).where(OrbitalRecord.object_id == "99999")))
    assert len(records) == 1
    assert records[0].validation_status == "malformed_line_prefix"


def test_ingest_handles_missing_tle_lines():
    session = _make_session()

    fake_result = SpaceTrackFetchResult(
        success=True, status="ok",
        raw_records=[{"NORAD_CAT_ID": "12345", "OBJECT_NAME": "NO TLE"}],
    )

    with patch("backend.services.ingestion.fetch_gp_data", return_value=fake_result):
        result = ingest_from_spacetrack(session, "user", "pass")

    assert result.skipped_missing_tle == 1
    assert result.saved_valid == 0

    records = list(session.scalars(select(OrbitalRecord).where(OrbitalRecord.object_id == "12345")))
    assert records[0].validation_status == "missing_tle_lines"


def test_ingest_propagates_login_failure():
    session = _make_session()

    fake_result = SpaceTrackFetchResult(success=False, status="login_failed", raw_records=None)

    with patch("backend.services.ingestion.fetch_gp_data", return_value=fake_result):
        result = ingest_from_spacetrack(session, "baduser", "badpass")

    assert result.success is False
    assert result.status == "login_failed"
    assert result.total_records == 0