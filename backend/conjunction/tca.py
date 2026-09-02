import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from scipy.optimize import minimize_scalar
from backend.orbital.propagation import propagate


@dataclass
class TCAResult:
    object_a: str
    object_b: str
    tca_utc: datetime
    miss_distance_km: float
    relative_velocity_km_s: float
    converged: bool
    refinement_status: str


def _distance_at_offset(offset_seconds, object_id_a, line1_a, line2_a,
                         object_id_b, line1_b, line2_b, reference_time) -> float:
    t = reference_time + timedelta(seconds=offset_seconds)
    result_a = propagate(object_id_a, 0, line1_a, line2_a, t)
    result_b = propagate(object_id_b, 0, line1_b, line2_b, t)

    if result_a.propagation_status != "ok" or result_b.propagation_status != "ok":
        return float("inf")

    return math.sqrt(
        (result_a.x_km - result_b.x_km) ** 2 +
        (result_a.y_km - result_b.y_km) ** 2 +
        (result_a.z_km - result_b.z_km) ** 2
    )


def refine_tca(
    object_id_a: str, line1_a: str, line2_a: str,
    object_id_b: str, line1_b: str, line2_b: str,
    window_start_utc: datetime, window_end_utc: datetime,
) -> TCAResult:
    """Numerically refines the coarse-grid minimum to the true time of closest approach."""
    reference_time = window_start_utc
    bound_seconds = (window_end_utc - window_start_utc).total_seconds()

    optimization = minimize_scalar(
        _distance_at_offset,
        bounds=(0.0, bound_seconds),
        method="bounded",
        args=(object_id_a, line1_a, line2_a, object_id_b, line1_b, line2_b, reference_time),
        options={"xatol": 0.01},
    )

    tca_utc = reference_time + timedelta(seconds=optimization.x)
    miss_distance_km = optimization.fun

    result_a = propagate(object_id_a, 0, line1_a, line2_a, tca_utc)
    result_b = propagate(object_id_b, 0, line1_b, line2_b, tca_utc)

    if result_a.propagation_status != "ok" or result_b.propagation_status != "ok":
        return TCAResult(
            object_a=object_id_a, object_b=object_id_b, tca_utc=tca_utc,
            miss_distance_km=miss_distance_km, relative_velocity_km_s=0.0,
            converged=False, refinement_status="propagation_failed_at_tca",
        )

    relative_velocity_km_s = math.sqrt(
        (result_a.vx_km_s - result_b.vx_km_s) ** 2 +
        (result_a.vy_km_s - result_b.vy_km_s) ** 2 +
        (result_a.vz_km_s - result_b.vz_km_s) ** 2
    )

    return TCAResult(
        object_a=object_id_a, object_b=object_id_b, tca_utc=tca_utc,
        miss_distance_km=miss_distance_km,
        relative_velocity_km_s=relative_velocity_km_s,
        converged=bool(optimization.success),
        refinement_status="ok" if optimization.success else "did_not_converge",
    )