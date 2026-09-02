import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from backend.orbital.propagation import propagate

_MU_KM3_S2 = 398600.8  # WGS72 gravitational parameter, matches propagation.py


@dataclass
class CandidateApproach:
    object_a: str
    object_b: str
    approx_time_utc: datetime
    approx_distance_km: float
    window_start_utc: datetime
    window_end_utc: datetime


def _parse_mean_motion_and_eccentricity(line2: str) -> tuple[float, float]:
    eccentricity_str = line2[26:33].strip()
    eccentricity = float(f"0.{eccentricity_str}")
    mean_motion_rev_day = float(line2[52:63].strip())
    return mean_motion_rev_day, eccentricity


def orbital_extent_km(line2: str) -> tuple[float, float]:
    """perigee radius, apogee radius"""
    mean_motion_rev_day, eccentricity = _parse_mean_motion_and_eccentricity(line2)
    n_rad_s = mean_motion_rev_day * 2 * math.pi / 86400.0
    semi_major_axis_km = (_MU_KM3_S2 / (n_rad_s ** 2)) ** (1 / 3)
    perigee_km = semi_major_axis_km * (1 - eccentricity)
    apogee_km = semi_major_axis_km * (1 + eccentricity)
    return perigee_km, apogee_km


def might_conjunct(line2_a: str, line2_b: str, margin_km: float = 200.0) -> bool:
    """Coarse filter: can these two orbits' radial ranges ever overlap?"""
    perigee_a, apogee_a = orbital_extent_km(line2_a)
    perigee_b, apogee_b = orbital_extent_km(line2_b)

    lo_a, hi_a = perigee_a - margin_km, apogee_a + margin_km
    lo_b, hi_b = perigee_b - margin_km, apogee_b + margin_km

    return lo_a <= hi_b and lo_b <= hi_a


def _distance_km(pos_a: tuple[float, float, float], pos_b: tuple[float, float, float]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(pos_a, pos_b)))


def screen_pair(
    object_id_a: str, line1_a: str, line2_a: str,
    object_id_b: str, line1_b: str, line2_b: str,
    start_time_utc: datetime, end_time_utc: datetime,
    step_seconds: int = 60, threshold_km: float = 100.0,
) -> list[CandidateApproach]:
    """Fine screening: sample relative distance over the window, flag local minima under threshold."""
    times: list[datetime] = []
    distances: list[float] = []

    t = start_time_utc
    while t <= end_time_utc:
        result_a = propagate(object_id_a, 0, line1_a, line2_a, t)
        result_b = propagate(object_id_b, 0, line1_b, line2_b, t)

        if result_a.propagation_status == "ok" and result_b.propagation_status == "ok":
            distance = _distance_km(
                (result_a.x_km, result_a.y_km, result_a.z_km),
                (result_b.x_km, result_b.y_km, result_b.z_km),
            )
            times.append(t)
            distances.append(distance)

        t += timedelta(seconds=step_seconds)

    candidates: list[CandidateApproach] = []
    for i in range(1, len(distances) - 1):
        is_local_min = distances[i] <= distances[i - 1] and distances[i] <= distances[i + 1]
        if is_local_min and distances[i] < threshold_km:
            candidates.append(CandidateApproach(
                object_a=object_id_a,
                object_b=object_id_b,
                approx_time_utc=times[i],
                approx_distance_km=distances[i],
                window_start_utc=times[i - 1],
                window_end_utc=times[i + 1],
            ))

    return candidates