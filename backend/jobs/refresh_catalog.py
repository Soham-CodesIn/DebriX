import itertools
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.conjunction.screening import might_conjunct, screen_pair
from backend.conjunction.tca import refine_tca
from backend.data.repository import (
    get_latest_record,
    save_alert,
    save_conjunction,
    save_propagation_state,
    save_risk_assessment,
    save_risk_feature,
)
from backend.orbital.propagation import propagate
from backend.risk.engine import assess_risk
from backend.services.ingestion import ingest_from_spacetrack

ALERT_RISK_LEVELS = {"HIGH", "CRITICAL"}


@dataclass
class RefreshResult:
    success: bool
    status: str
    objects_ingested: int = 0
    objects_propagated: int = 0
    pairs_coarse_filtered_in: int = 0
    conjunctions_found: int = 0
    alerts_created: int = 0
    conjunction_ids: list[str] = field(default_factory=list)


def _make_conjunction_id(object_a: str, object_b: str, tca_utc: datetime) -> str:
    ordered_a, ordered_b = sorted([object_a, object_b])
    return f"{ordered_a}_{ordered_b}_{tca_utc.strftime('%Y%m%dT%H%M%S')}"


def run_refresh_catalog(
    session: Session,
    spacetrack_username: str,
    spacetrack_password: str,
    norad_ids: list[str] | None = None,
    ingest_limit: int = 100,
    screening_window_hours: int = 24,
    screening_step_seconds: int = 60,
    screening_threshold_km: float = 100.0,
    coarse_filter_margin_km: float = 200.0,
) -> RefreshResult:
    """
    Runs the full DebriX pipeline all at once: ingest the latest catalog data from
    Space-Track, propagate every validly-parsed object to now, screen all
    pairs for close approaches, refine each candidate's TCA, score risk,
    and raise alerts for HIGH/CRITICAL conjunctions.
    """
    ingestion_result = ingest_from_spacetrack(
        session, spacetrack_username, spacetrack_password,
        norad_ids=norad_ids, limit=ingest_limit,
    )

    if not ingestion_result.success:
        return RefreshResult(success=False, status=ingestion_result.status)

    now = datetime.now(timezone.utc)
    window_end = now + timedelta(hours=screening_window_hours)

    # Only objects with a valid, parseable latest TLE can be propagated or
    valid_objects: dict[str, tuple[str, str]] = {}
    for object_id in ingestion_result.processed_object_ids:
        latest_record = get_latest_record(session, object_id)
        if latest_record and latest_record.validation_status == "valid" \
                and latest_record.tle_line1 and latest_record.tle_line2:
            valid_objects[object_id] = (latest_record.tle_line1, latest_record.tle_line2)

    result = RefreshResult(
        success=True, status="ok",
        objects_ingested=len(ingestion_result.processed_object_ids),
    )

    for object_id, (line1, line2) in valid_objects.items():
        propagation = propagate(object_id, source_record_id=0, line1=line1, line2=line2,
                                 target_time_utc=now)
        if propagation.propagation_status == "ok":
            save_propagation_state(
                session, object_id=object_id, source_record_id=0, time_utc=now,
                x_km=propagation.x_km, y_km=propagation.y_km, z_km=propagation.z_km,
                vx_km_s=propagation.vx_km_s, vy_km_s=propagation.vy_km_s, vz_km_s=propagation.vz_km_s,
                frame=propagation.frame, propagation_status=propagation.propagation_status,
            )
            result.objects_propagated += 1

    for (object_a, (line1_a, line2_a)), (object_b, (line1_b, line2_b)) in itertools.combinations(
        valid_objects.items(), 2
    ):
        if not might_conjunct(line2_a, line2_b, margin_km=coarse_filter_margin_km):
            continue
        result.pairs_coarse_filtered_in += 1

        candidates = screen_pair(
            object_a, line1_a, line2_a, object_b, line1_b, line2_b,
            start_time_utc=now, end_time_utc=window_end,
            step_seconds=screening_step_seconds, threshold_km=screening_threshold_km,
        )

        for candidate in candidates:
            tca_result = refine_tca(
                object_a, line1_a, line2_a, object_b, line1_b, line2_b,
                window_start_utc=candidate.window_start_utc,
                window_end_utc=candidate.window_end_utc,
            )

            conjunction_id = _make_conjunction_id(object_a, object_b, tca_result.tca_utc)

            save_conjunction(
                session, conjunction_id=conjunction_id,
                object_a=object_a, object_b=object_b, tca=tca_result.tca_utc,
                miss_distance_km=tca_result.miss_distance_km,
                relative_velocity_km_s=tca_result.relative_velocity_km_s,
            )
            result.conjunctions_found += 1
            result.conjunction_ids.append(conjunction_id)

            risk = assess_risk(conjunction_id, tca_result)

            save_risk_assessment(
                session, conjunction_id=conjunction_id, pc=risk.pc, pc_status=risk.pc_status,
                f_value=risk.f_value, risk_level=risk.risk_level, confidence=risk.confidence,
                methodology_version=risk.methodology_version,
            )

            save_risk_feature(session, conjunction_id, "normalized_distance",
                               risk.features.miss_distance_km, risk.features.normalized_distance)
            save_risk_feature(session, conjunction_id, "normalized_velocity",
                               risk.features.relative_velocity_km_s, risk.features.normalized_velocity)
            save_risk_feature(session, conjunction_id, "hbr_ratio",
                               risk.features.combined_hbr_km, risk.features.hbr_ratio)

            if risk.risk_level in ALERT_RISK_LEVELS:
                save_alert(session, conjunction_id=conjunction_id, severity=risk.risk_level)
                result.alerts_created += 1

    return result