from flask import Blueprint, jsonify

from backend.data import database
from backend.data.repository import (
    get_all_conjunctions,
    get_conjunction,
    get_risk_assessment,
    get_risk_features,
)

conjunction_bp = Blueprint("conjunction", __name__)


def _serialize_conjunction(c):
    return {
        "conjunction_id": c.conjunction_id,
        "object_a": c.object_a,
        "object_b": c.object_b,
        "tca": c.tca.isoformat(),
        "miss_distance_km": c.miss_distance_km,
        "relative_velocity_km_s": c.relative_velocity_km_s,
    }


@conjunction_bp.get("/conjunctions")
def list_conjunctions():
    session = database.SessionLocal()
    try:
        conjunctions = get_all_conjunctions(session)
        return jsonify([_serialize_conjunction(c) for c in conjunctions])
    finally:
        session.close()


@conjunction_bp.get("/conjunctions/<conjunction_id>")
def get_conjunction_detail(conjunction_id):
    session = database.SessionLocal()
    try:
        conjunction = get_conjunction(session, conjunction_id)
        if conjunction is None:
            return jsonify({"error": "conjunction_not_found"}), 404

        payload = _serialize_conjunction(conjunction)

        # Risk data is optional -- may not exist yet if the risk engine
        # hasn't processed this conjunction. Returning null rather than
        # erroring keeps this endpoint usable throughout the pipeline.
        risk_assessment = get_risk_assessment(session, conjunction_id)
        payload["risk_assessment"] = None
        if risk_assessment:
            payload["risk_assessment"] = {
                "pc": risk_assessment.pc,
                "pc_status": risk_assessment.pc_status,
                "f_value": risk_assessment.f_value,
                "risk_level": risk_assessment.risk_level,
                "confidence": risk_assessment.confidence,
                "methodology_version": risk_assessment.methodology_version,
            }

        features = get_risk_features(session, conjunction_id)
        payload["risk_features"] = [
            {
                "feature_name": f.feature_name,
                "raw_value": f.raw_value,
                "normalized_value": f.normalized_value,
            }
            for f in features
        ]

        return jsonify(payload)
    finally:
        session.close()