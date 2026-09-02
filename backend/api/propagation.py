from flask import Blueprint, jsonify

from backend.data import database
from backend.data.repository import get_latest_propagation_state, get_object

propagation_bp = Blueprint("propagation", __name__)


@propagation_bp.get("/objects/<object_id>/propagation")
def get_propagation(object_id):
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
            "position_km": {"x": state.x_km, "y": state.y_km, "z": state.z_km},
            "velocity_km_s": {"x": state.vx_km_s, "y": state.vy_km_s, "z": state.vz_km_s},
            "frame": state.frame,
            "propagation_status": state.propagation_status,
        })
    finally:
        session.close()