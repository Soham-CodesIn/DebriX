from datetime import datetime, timezone
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import backend.data.models  # noqa: F401  ensures models are registered on Base
from backend.data.database import Base
from backend.data.models import Alert, Conjunction, RiskAssessment
from backend.jobs.refresh_catalog import run_refresh_catalog
from backend.data.repository import save_object, save_raw_orbital_record
from backend.services.ingestion import IngestionResult

LINE1 = "1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753"
LINE2 = "2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667"


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def _seed_object(session, object_id):
    save_object(session, object_id=object_id, name=f"Object {object_id}", object_type="PAYLOAD")
    save_raw_orbital_record(
        session, object_id=object_id,
        epoch_utc=datetime(2000, 6, 28, tzinfo=timezone.utc),
        source="spacetrack", retrieved_at=datetime.now(timezone.utc),
        raw_record="{}", validation_status="valid",
        tle_line1=LINE1, tle_line2=LINE2,
    )


def test_run_refresh_catalog_produces_conjunction_and_alert():
    session = _make_session()

    # Two "different" objects sharing an identical orbit -- guarantees a
    # zero-distance close approach, same trick used in test_conjunction.py.
    _seed_object(session, "00005")
    _seed_object(session, "00006")

    fake_ingestion = IngestionResult(
        success=True, status="ok", total_records=2, saved_valid=2,
        processed_object_ids=["00005", "00006"],
    )

    with patch("backend.jobs.refresh_catalog.ingest_from_spacetrack", return_value=fake_ingestion):
        result = run_refresh_catalog(
            session, "user", "pass",
            screening_window_hours=1, screening_step_seconds=300,
        )

    assert result.success is True
    assert result.objects_ingested == 2
    assert result.objects_propagated == 2
    assert result.pairs_coarse_filtered_in == 1
    assert result.conjunctions_found > 0
    assert result.alerts_created > 0

    conjunctions = list(session.scalars(select(Conjunction)))
    assert len(conjunctions) == result.conjunctions_found
    assert conjunctions[0].miss_distance_km < 1e-3

    risk_assessments = list(session.scalars(select(RiskAssessment)))
    assert len(risk_assessments) == result.conjunctions_found
    assert risk_assessments[0].risk_level == "CRITICAL"

    alerts = list(session.scalars(select(Alert)))
    assert len(alerts) == result.alerts_created
    assert alerts[0].severity == "CRITICAL"


def test_run_refresh_catalog_stops_early_on_ingestion_failure():
    session = _make_session()

    fake_ingestion = IngestionResult(success=False, status="login_failed")

    with patch("backend.jobs.refresh_catalog.ingest_from_spacetrack", return_value=fake_ingestion):
        result = run_refresh_catalog(session, "baduser", "badpass")

    assert result.success is False
    assert result.status == "login_failed"
    assert result.objects_propagated == 0
    assert result.conjunctions_found == 0


def test_run_refresh_catalog_skips_pairs_that_cannot_conjunct():
    session = _make_session()

    _seed_object(session, "00005")

    # A stable near-circular LEO orbit whose radial range never overlaps
    # the eccentric reference orbit above.
    leo_line2 = "2 25544  51.6400 208.9163 0006317  86.7862  32.8481 15.50377579123456"
    save_object(session, object_id="25544", name="ISS", object_type="PAYLOAD")
    save_raw_orbital_record(
        session, object_id="25544", epoch_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
        source="spacetrack", retrieved_at=datetime.now(timezone.utc),
        raw_record="{}", validation_status="valid",
        tle_line1=LINE1, tle_line2=leo_line2,
    )

    fake_ingestion = IngestionResult(
        success=True, status="ok", total_records=2, saved_valid=2,
        processed_object_ids=["00005", "25544"],
    )

    with patch("backend.jobs.refresh_catalog.ingest_from_spacetrack", return_value=fake_ingestion):
        result = run_refresh_catalog(session, "user", "pass", coarse_filter_margin_km=50.0)

    assert result.pairs_coarse_filtered_in == 0
    assert result.conjunctions_found == 0
    assert result.alerts_created == 0