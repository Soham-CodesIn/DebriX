from flask import Blueprint, jsonify

from backend.data import database
from backend.data.repository import get_all_objects, get_latest_record, get_object

objects_bp = Blueprint("objects", __name__)


def _serialize_object(obj):
    return {
        "object_id": obj.object_id,
        "name": obj.name,
        "object_type": obj.object_type,
        "created_at": obj.created_at.isoformat() if obj.created_at else None,
    }


@objects_bp.get("/objects")
def list_objects():
    session = database.SessionLocal()
    try:
        objects = get_all_objects(session)
        return jsonify([_serialize_object(o) for o in objects])
    finally:
        session.close()


@objects_bp.get("/objects/<object_id>")
def get_object_detail(object_id):
    session = database.SessionLocal()
    try:
        obj = get_object(session, object_id)
        if obj is None:
            return jsonify({"error": "object_not_found"}), 404

        payload = _serialize_object(obj)

        latest_record = get_latest_record(session, object_id)
        payload["latest_record"] = None
        if latest_record:
            payload["latest_record"] = {
                "record_id": latest_record.record_id,
                "epoch_utc": latest_record.epoch_utc.isoformat() if latest_record.epoch_utc else None,
                "source": latest_record.source,
                "validation_status": latest_record.validation_status,
            }

        return jsonify(payload)
    finally:
        session.close()