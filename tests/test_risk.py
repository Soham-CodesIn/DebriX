import pytest
from datetime import datetime, timezone

from backend.conjunction.tca import TCAResult
from backend.risk.engine import assess_risk
from backend.risk.features import compute_features


def _make_tca_result(miss_distance_km, relative_velocity_km_s, converged=True):
    return TCAResult(
        object_a="A", object_b="B",
        tca_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
        miss_distance_km=miss_distance_km,
        relative_velocity_km_s=relative_velocity_km_s,
        converged=converged,
        refinement_status="ok" if converged else "did_not_converge",
    )


def test_features_normalize_within_bounds():
    tca_result = _make_tca_result(miss_distance_km=2.5, relative_velocity_km_s=7.5)
    features = compute_features("conj-1", tca_result)

    assert 0.0 <= features.normalized_distance <= 1.0
    assert 0.0 <= features.normalized_velocity <= 1.0
    assert features.hbr_ratio > 0


def test_very_close_approach_triggers_critical_override():
    # miss distance smaller than default combined hard-body radius (20 m = 0.02 km)
    tca_result = _make_tca_result(miss_distance_km=0.005, relative_velocity_km_s=1.0)
    result = assess_risk("conj-critical", tca_result)

    assert result.f_value == pytest.approx(1.0)
    assert result.risk_level == "CRITICAL"


def test_distant_slow_approach_is_low_risk():
    tca_result = _make_tca_result(miss_distance_km=50.0, relative_velocity_km_s=0.5)
    result = assess_risk("conj-low", tca_result)

    assert result.risk_level == "LOW"


def test_pc_is_null_with_explanatory_status():
    tca_result = _make_tca_result(miss_distance_km=3.0, relative_velocity_km_s=5.0)
    result = assess_risk("conj-pc", tca_result)

    assert result.pc is None
    assert result.pc_status == "unavailable_no_covariance_data"


def test_unconverged_tca_downgrades_confidence_and_risk_level():
    tca_result = _make_tca_result(miss_distance_km=1.0, relative_velocity_km_s=5.0, converged=False)
    result = assess_risk("conj-unconverged", tca_result)

    assert result.confidence == "low"
    assert result.risk_level == "UNKNOWN"