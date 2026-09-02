from flask import Blueprint, jsonify

from backend.data import database
from backend.data.repository import get_open_alerts

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.get("/alerts")
def list_open_alerts():
    session = database.SessionLocal()
    try:
        alerts = get_open_alerts(session)
        return jsonify([
            {
                "alert_id": a.alert_id,
                "conjunction_id": a.conjunction_id,
                "severity": a.severity,
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "updated_at": a.updated_at.isoformat() if a.updated_at else None,
            }
            for a in alerts
        ])
    finally:
        session.close()