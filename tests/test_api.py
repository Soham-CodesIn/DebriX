from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.data import database
from backend.data.database import Base
import backend.data.models  # noqa: F401  ensures models are registered on Base


@pytest.fixture
def client():
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)

    # Swap the database module's engine/session factory so every route,
    # which looks these up via `database.SessionLocal()` at request time,
    # talks to this isolated in-memory DB instead of debrix.db.
    database.engine = test_engine
    database.SessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)

    from backend.app import create_app
    app = create_app()
    app.config.update({"TESTING": True})

    with app.test_client() as test_client:
        yield test_client


def _seed_object_and_conjunction():
    from backend.data.repository import (
        save_alert,
        save_conjunction,
        save_object,
        save_propagation_state,
        save_risk_assessment,
        save_risk_feature,
    )

    session = database.SessionLocal()

    save_object(session, object_id="25544", name="ISS", object_type="PAYLOAD")
    save_object(session, object_id="99999", name="Debris", object_type="DEBRIS")

    save_propagation_state(
        session, object_id="25544", source_record_id=1,
        time_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
        x_km=1.0, y_km=2.0, z_km=3.0,
        vx_km_s=0.1, vy_km_s=0.2, vz_km_s=0.3,
        frame="TEME", propagation_status="ok",
    )

    save_conjunction(
        session, conjunction_id="conj-1", object_a="25544", object_b="99999",
        tca=datetime(2026, 1, 1, 0, 5, tzinfo=timezone.utc),
        miss_distance_km=0.5, relative_velocity_km_s=7.0,
    )

    save_risk_assessment(
        session, conjunction_id="conj-1", pc=None,
        pc_status="unavailable_no_covariance_data",
        f_value=0.8, risk_level="HIGH", confidence="medium",
        methodology_version="deterministic-v1",
    )
    save_risk_feature(
        session, conjunction_id="conj-1", feature_name="normalized_distance",
        raw_value=0.5, normalized_value=0.9,
    )
    save_alert(session, conjunction_id="conj-1", severity="HIGH")

    session.close()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_list_and_get_object(client):
    _seed_object_and_conjunction()

    list_response = client.get("/objects")
    assert list_response.status_code == 200
    object_ids = {o["object_id"] for o in list_response.get_json()}
    assert {"25544", "99999"} <= object_ids

    detail_response = client.get("/objects/25544")
    assert detail_response.status_code == 200
    assert detail_response.get_json()["name"] == "ISS"


def test_get_object_not_found(client):
    response = client.get("/objects/doesnotexist")
    assert response.status_code == 404


def test_get_propagation(client):
    _seed_object_and_conjunction()

    response = client.get("/objects/25544/propagation")
    assert response.status_code == 200
    assert response.get_json()["position_km"]["x"] == 1.0


def test_get_propagation_not_found(client):
    _seed_object_and_conjunction()  # object exists, but has no propagation state

    response = client.get("/objects/99999/propagation")
    assert response.status_code == 404


def test_list_and_get_conjunction(client):
    _seed_object_and_conjunction()

    list_response = client.get("/conjunctions")
    assert list_response.status_code == 200
    assert len(list_response.get_json()) == 1

    detail_response = client.get("/conjunctions/conj-1")
    assert detail_response.status_code == 200
    body = detail_response.get_json()
    assert body["risk_assessment"]["risk_level"] == "HIGH"
    assert len(body["risk_features"]) == 1


def test_get_conjunction_not_found(client):
    response = client.get("/conjunctions/doesnotexist")
    assert response.status_code == 404


def test_list_open_alerts(client):
    _seed_object_and_conjunction()

    response = client.get("/alerts")
    assert response.status_code == 200
    alerts = response.get_json()
    assert len(alerts) == 1
    assert alerts[0]["status"] == "open"