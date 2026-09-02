from dataclasses import dataclass

from backend.conjunction.tca import TCAResult
from backend.risk.features import RiskFeatureSet, compute_features

METHODOLOGY_VERSION = "deterministic-v1"

_DISTANCE_WEIGHT = 0.7
_VELOCITY_WEIGHT = 0.3

_CRITICAL_THRESHOLD = 0.85
_HIGH_THRESHOLD = 0.6
_MEDIUM_THRESHOLD = 0.3


@dataclass
class RiskAssessmentResult:
    conjunction_id: str
    pc: float | None
    pc_status: str
    f_value: float
    risk_level: str
    confidence: str
    methodology_version: str
    features: RiskFeatureSet


def _risk_level_from_f_value(f_value: float) -> str:
    if f_value >= _CRITICAL_THRESHOLD:
        return "CRITICAL"
    if f_value >= _HIGH_THRESHOLD:
        return "HIGH"
    if f_value >= _MEDIUM_THRESHOLD:
        return "MEDIUM"
    return "LOW"


def assess_risk(
    conjunction_id: str, tca_result: TCAResult,
    combined_hbr_km: float = 0.02,
) -> RiskAssessmentResult:
    """
    Deterministic, physics-based risk scoring. No probability of collision (Pc) is
    computed since public TLE data carries no covariance/uncertainty information
    Pc is left null with an explanatory status rather than faked.
    """
    features = compute_features(conjunction_id, tca_result, combined_hbr_km)

    f_value = _DISTANCE_WEIGHT * features.normalized_distance + _VELOCITY_WEIGHT * features.normalized_velocity
    f_value = min(f_value, 1.0)

    # physical safety override if hard-body envelopes overlap at TCA, this is
    # effectively certain contact regardless of the weighted score above
    if features.hbr_ratio >= 1.0:
        f_value = 1.0

    risk_level = _risk_level_from_f_value(f_value)

    confidence = "medium"
    if not tca_result.converged:
        confidence = "low"
        risk_level = "UNKNOWN"

    return RiskAssessmentResult(
        conjunction_id=conjunction_id,
        pc=None,
        pc_status="unavailable_no_covariance_data",
        f_value=f_value,
        risk_level=risk_level,
        confidence=confidence,
        methodology_version=METHODOLOGY_VERSION,
        features=features,
    )