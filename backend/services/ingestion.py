import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.data.repository import save_object, save_raw_orbital_record
from backend.orbital.tle import parse_tle
from backend.services.spacetrack import fetch_gp_data


@dataclass
class IngestionResult:
    success: bool
    status: str
    total_records: int = 0
    saved_valid: int = 0
    saved_invalid: int = 0
    skipped_missing_tle: int = 0
    processed_object_ids: list[str] = field(default_factory=list)


def _extract_tle_lines(raw_record: dict) -> tuple[str | None, str | None]:
    return raw_record.get("TLE_LINE1"), raw_record.get("TLE_LINE2")


def ingest_from_spacetrack(
    session: Session,
    username: str,
    password: str,
    norad_ids: list[str] | None = None,
    limit: int = 100,
) -> IngestionResult:

    fetch_result = fetch_gp_data(username, password, norad_ids=norad_ids, limit=limit)

    if not fetch_result.success:
        return IngestionResult(success=False, status=fetch_result.status)

    raw_records = fetch_result.raw_records or []
    retrieved_at = datetime.now(timezone.utc)

    result = IngestionResult(success=True, status="ok", total_records=len(raw_records))

    for raw_record in raw_records:
        object_id = raw_record.get("NORAD_CAT_ID")
        if not object_id:
            result.skipped_missing_tle += 1
            continue

        line1, line2 = _extract_tle_lines(raw_record)

        if not line1 or not line2:
            save_object(
                session=session,
                object_id=object_id,
                name=raw_record.get("OBJECT_NAME"),
                object_type=raw_record.get("OBJECT_TYPE"),
            )
            save_raw_orbital_record(
                session=session,
                object_id=object_id,
                epoch_utc=None,
                source="spacetrack",
                retrieved_at=retrieved_at,
                raw_record=json.dumps(raw_record),
                validation_status="missing_tle_lines",
            )
            result.skipped_missing_tle += 1
            result.processed_object_ids.append(object_id)
            continue

        parsed = parse_tle(line1, line2)

        save_object(
            session=session,
            object_id=object_id,
            name=raw_record.get("OBJECT_NAME"),
            object_type=raw_record.get("OBJECT_TYPE"),
        )

        save_raw_orbital_record(
            session=session,
            object_id=object_id,
            epoch_utc=parsed.epoch_utc if parsed.is_valid else None,
            source="spacetrack",
            retrieved_at=retrieved_at,
            raw_record=json.dumps(raw_record),
            validation_status=parsed.validation_status,
            tle_line1=line1,
            tle_line2=line2,
        )

        if parsed.is_valid:
            result.saved_valid += 1
        else:
            result.saved_invalid += 1

        result.processed_object_ids.append(object_id)

    return result