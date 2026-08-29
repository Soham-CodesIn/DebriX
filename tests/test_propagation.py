from datetime import datetime, timezone

import pytest

from backend.orbital.propagation import propagate

# Official Vallado SGP4 verification test vector (satellite 00005, 58002B)
LINE1 = "1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753"
LINE2 = "2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667"

# Reference output from the sgp4 library's own documented example:
# propagate to 2000-06-29 12:50:19 UTC
EXPECTED_POSITION_KM = (5576.056952400586, -3999.371134576452, -1521.9571594376037)
EXPECTED_VELOCITY_KM_S = (4.772627303379319, 5.119817120959591, 4.275553909172126)


def test_propagate_matches_reference_output():
    target_time = datetime(2000, 6, 29, 12, 50, 19, tzinfo=timezone.utc)

    result = propagate("00005", source_record_id=1, line1=LINE1, line2=LINE2,
                        target_time_utc=target_time)

    assert result.propagation_status == "ok"
    assert result.frame == "TEME"

    assert result.x_km == pytest.approx(EXPECTED_POSITION_KM[0], rel=1e-3)
    assert result.y_km == pytest.approx(EXPECTED_POSITION_KM[1], rel=1e-3)
    assert result.z_km == pytest.approx(EXPECTED_POSITION_KM[2], rel=1e-3)

    assert result.vx_km_s == pytest.approx(EXPECTED_VELOCITY_KM_S[0], rel=1e-3)
    assert result.vy_km_s == pytest.approx(EXPECTED_VELOCITY_KM_S[1], rel=1e-3)
    assert result.vz_km_s == pytest.approx(EXPECTED_VELOCITY_KM_S[2], rel=1e-3)


def test_propagate_preserves_identifiers():
    target_time = datetime(2000, 6, 29, 12, 50, 19, tzinfo=timezone.utc)

    result = propagate("00005", source_record_id=42, line1=LINE1, line2=LINE2,
                        target_time_utc=target_time)

    assert result.object_id == "00005"
    assert result.source_record_id == 42
    assert result.time_utc == target_time