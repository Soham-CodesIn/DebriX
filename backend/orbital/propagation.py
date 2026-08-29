from dataclasses import dataclass
from datetime import datetime, timezone
from sgp4.api import Satrec, jday, WGS72


@dataclass
class PropagationResult:
    object_id: str
    source_record_id: int
    time_utc: datetime
    x_km: float | None
    y_km: float | None
    z_km: float | None
    vx_km_s: float | None
    vy_km_s: float | None
    vz_km_s: float | None
    frame: str
    propagation_status: str


_SGP4_ERROR_MESSAGES = {
    1: "mean_eccentricity_out_of_range",
    2: "mean_motion_negative",
    3: "eccentricity_out_of_range",
    4: "semi_latus_rectum_negative",
    5: "epoch_elements_negative_mean_motion",
    6: "satellite_decayed",
}


def propagate(object_id: str, source_record_id: int, line1: str, line2: str,
              target_time_utc: datetime) -> PropagationResult:
    satellite = Satrec.twoline2rv(line1, line2, WGS72)

    jd, fr = jday(
        target_time_utc.year, target_time_utc.month, target_time_utc.day,
        target_time_utc.hour, target_time_utc.minute,
        target_time_utc.second + target_time_utc.microsecond / 1e6,
    )

    error_code, position, velocity = satellite.sgp4(jd, fr)

    if error_code != 0:
        return PropagationResult(
            object_id=object_id,
            source_record_id=source_record_id,
            time_utc=target_time_utc,
            x_km=None, y_km=None, z_km=None,
            vx_km_s=None, vy_km_s=None, vz_km_s=None,
            frame="TEME",
            propagation_status=_SGP4_ERROR_MESSAGES.get(error_code, f"sgp4_error_{error_code}"),
        )

    return PropagationResult(
        object_id=object_id,
        source_record_id=source_record_id,
        time_utc=target_time_utc,
        x_km=position[0], y_km=position[1], z_km=position[2],
        vx_km_s=velocity[0], vy_km_s=velocity[1], vz_km_s=velocity[2],
        frame="TEME",
        propagation_status="ok",
    )