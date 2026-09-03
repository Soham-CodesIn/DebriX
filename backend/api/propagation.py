from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

from backend.data import database
from backend.data.repository import (
    get_latest_propagation_state,
    get_latest_record,
    get_object,
    get_record_history,
)
from backend.orbital.propagation import propagate


propagation_bp = Blueprint("propagation", __name__)


def _parse_datetime(value):
    """
    Parse an ISO-8601 datetime.

    Examples accepted:
        2026-09-03T13:59:21
        2026-09-03T13:59:21.523923
        2026-09-03T13:59:21Z
    """
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)

        return parsed

    except ValueError:
        return None


def _get_usable_tle(session, object_id):
    """
    Get the newest orbital record that contains both TLE lines.

    We first check the latest record, then fall back through history.
    """
    latest = get_latest_record(session, object_id)

    if (
        latest is not None
        and latest.tle_line1
        and latest.tle_line2
    ):
        return latest

    history = get_record_history(session, object_id)

    for record in history:
        if record.tle_line1 and record.tle_line2:
            return record

    return None


def _serialize_propagation(result):
    return {
        "object_id": result.object_id,
        "source_record_id": result.source_record_id,
        "time_utc": result.time_utc.isoformat(),
        "position_km": {
            "x": result.x_km,
            "y": result.y_km,
            "z": result.z_km,
        },
        "velocity_km_s": {
            "x": result.vx_km_s,
            "y": result.vy_km_s,
            "z": result.vz_km_s,
        },
        "frame": result.frame,
        "propagation_status": result.propagation_status,
    }


@propagation_bp.get("/objects/<object_id>/propagation")
def get_propagation(object_id):
    """
    Return the latest stored propagation state.
    """
    session = database.SessionLocal()

    try:
        obj = get_object(session, object_id)

        if obj is None:
            return jsonify({"error": "object_not_found"}), 404

        state = get_latest_propagation_state(session, object_id)

        if state is None:
            return jsonify({"error": "no_propagation_state"}), 404

        return jsonify({
            "object_id": state.object_id,
            "time_utc": state.time_utc.isoformat(),
            "position_km": {
                "x": state.x_km,
                "y": state.y_km,
                "z": state.z_km,
            },
            "velocity_km_s": {
                "x": state.vx_km_s,
                "y": state.vy_km_s,
                "z": state.vz_km_s,
            },
            "frame": state.frame,
            "propagation_status": state.propagation_status,
        })

    finally:
        session.close()


@propagation_bp.get("/objects/<object_id>/trajectory")
def get_trajectory(object_id):
    """
    Generate a real SGP4 trajectory from the object's latest TLE.

    Query parameters:

        start   ISO-8601 UTC start time
        end     ISO-8601 UTC end time
        steps   Number of propagation points

    Example:

        /objects/82/trajectory
            ?start=2026-09-03T13:00:00
            &end=2026-09-03T15:00:00
            &steps=120
    """

    session = database.SessionLocal()

    try:
        obj = get_object(session, object_id)

        if obj is None:
            return jsonify({"error": "object_not_found"}), 404

        record = _get_usable_tle(session, object_id)

        if record is None:
            return jsonify({
                "error": "no_tle_available",
                "object_id": object_id,
            }), 404

        start_time = _parse_datetime(request.args.get("start"))
        end_time = _parse_datetime(request.args.get("end"))

        # If the frontend doesn't provide a time range,
        # use the TLE epoch when available.
        if start_time is None:
            if record.epoch_utc is not None:
                start_time = record.epoch_utc
            else:
                start_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=30)

        if end_time is None:
            end_time = start_time + timedelta(hours=2)

        if end_time <= start_time:
            return jsonify({
                "error": "invalid_time_range",
                "message": "end must be after start",
            }), 400

        try:
            steps = int(request.args.get("steps", 120))
        except ValueError:
            return jsonify({
                "error": "invalid_steps",
                "message": "steps must be an integer",
            }), 400

        # Protect the backend from accidentally huge requests.
        steps = max(2, min(steps, 500))

        total_seconds = (end_time - start_time).total_seconds()
        interval_seconds = total_seconds / (steps - 1)

        points = []

        for index in range(steps):
            target_time = start_time + timedelta(
                seconds=index * interval_seconds
            )

            result = propagate(
                object_id=object_id,
                source_record_id=record.record_id,
                line1=record.tle_line1,
                line2=record.tle_line2,
                target_time_utc=target_time,
            )

            points.append(_serialize_propagation(result))

        successful_points = [
            point
            for point in points
            if point["propagation_status"] == "ok"
        ]

        return jsonify({
            "object_id": object_id,
            "source_record_id": record.record_id,
            "tle_epoch_utc": (
                record.epoch_utc.isoformat()
                if record.epoch_utc is not None
                else None
            ),
            "frame": "TEME",
            "start_utc": start_time.isoformat(),
            "end_utc": end_time.isoformat(),
            "requested_steps": steps,
            "successful_points": len(successful_points),
            "points": points,
        })

    finally:
        session.close()