from flask import Blueprint, jsonify

from backend.data import database
from backend.data.repository import (
    get_all_conjunctions,
    get_conjunction,
    get_risk_assessment,
    get_risk_features,
)

conjunction_bp = Blueprint("conjunction", __name__)


def _serialize_conjunction(c, session=None):
    payload = {
        "conjunction_id": c.conjunction_id,
        "object_a": c.object_a,
        "object_b": c.object_b,
        "tca": c.tca.isoformat(),
        "miss_distance_km": c.miss_distance_km,
        "relative_velocity_km_s": c.relative_velocity_km_s,
    }

    # Include risk information when a database session is available.
    if session is not None:
        risk_assessment = get_risk_assessment(
            session,
            c.conjunction_id
        )

        if risk_assessment:
            payload["risk_assessment"] = {
                "pc": risk_assessment.pc,
                "pc_status": risk_assessment.pc_status,
                "f_value": risk_assessment.f_value,
                "risk_level": risk_assessment.risk_level,
                "confidence": risk_assessment.confidence,
                "methodology_version": risk_assessment.methodology_version,
            }
        else:
            payload["risk_assessment"] = None

    return payload


@conjunction_bp.get("/conjunctions")
def list_conjunctions():
    session = database.SessionLocal()

    try:
        conjunctions = get_all_conjunctions(session)

        return jsonify([
            _serialize_conjunction(c, session)
            for c in conjunctions
        ])

    finally:
        session.close()


@conjunction_bp.get("/conjunctions/<conjunction_id>")
def get_conjunction_detail(conjunction_id):
    session = database.SessionLocal()

    try:
        conjunction = get_conjunction(
            session,
            conjunction_id
        )

        if conjunction is None:
            return jsonify({
                "error": "conjunction_not_found"
            }), 404

        payload = _serialize_conjunction(
            conjunction,
            session
        )

        features = get_risk_features(
            session,
            conjunction_id
        )

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