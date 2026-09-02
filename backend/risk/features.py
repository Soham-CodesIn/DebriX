from dataclasses import dataclass

from backend.conjunction.tca import TCAResult

PROXIMITY_SCALE_KM = 5.0
VELOCITY_SCALE_KM_S = 15.0
DEFAULT_COMBINED_HBR_KM = 0.02  # 20 m combined hard-body radius, conservative default absent object-specific size data


@dataclass
class RiskFeatureSet:
    conjunction_id: str
    miss_distance_km: float
    relative_velocity_km_s: float
    combined_hbr_km: float
    hbr_ratio: float
    normalized_distance: float
    normalized_velocity: float


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def compute_features(
    conjunction_id: str, tca_result: TCAResult,
    combined_hbr_km: float = DEFAULT_COMBINED_HBR_KM,
) -> RiskFeatureSet:
    miss_distance_km = max(tca_result.miss_distance_km, 1e-9)  # guard against div by zero

    normalized_distance = _clamp(1 - miss_distance_km / PROXIMITY_SCALE_KM)
    normalized_velocity = _clamp(tca_result.relative_velocity_km_s / VELOCITY_SCALE_KM_S)
    hbr_ratio = combined_hbr_km / miss_distance_km

    return RiskFeatureSet(
        conjunction_id=conjunction_id,
        miss_distance_km=tca_result.miss_distance_km,
        relative_velocity_km_s=tca_result.relative_velocity_km_s,
        combined_hbr_km=combined_hbr_km,
        hbr_ratio=hbr_ratio,
        normalized_distance=normalized_distance,
        normalized_velocity=normalized_velocity,
    )