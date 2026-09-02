from datetime import datetime, timedelta, timezone
import pytest
from backend.conjunction.screening import might_conjunct, orbital_extent_km, screen_pair
from backend.conjunction.tca import refine_tca

LINE1 = "1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753"
LINE2 = "2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667"

# A near-circular LEO orbit far from the object above — should never conjunct with it.
LEO_LINE2 = "2 25544  51.6400 208.9163 0006317  86.7862  32.8481 15.50377579123456"


def test_orbital_extent_reasonable_for_known_orbit():
    perigee_km, apogee_km = orbital_extent_km(LINE2)
    assert perigee_km < apogee_km
    assert 6000 < perigee_km < 50000  # sanity bounds, this is a fairly eccentric orbit


def test_might_conjunct_true_for_same_orbit():
    assert might_conjunct(LINE2, LINE2) is True


def test_might_conjunct_false_for_disjoint_orbits():
    assert might_conjunct(LINE2, LEO_LINE2, margin_km=50.0) is False


def test_screen_pair_finds_zero_distance_for_identical_object():
    start = datetime(2000, 6, 29, 12, 0, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=2)

    candidates = screen_pair("A", LINE1, LINE2, "B", LINE1, LINE2, start, end,
                              step_seconds=300, threshold_km=1.0)

    assert len(candidates) > 0
    assert candidates[0].approx_distance_km == pytest.approx(0.0, abs=1e-6)


def test_refine_tca_converges_to_zero_distance_for_identical_object():
    window_start = datetime(2000, 6, 29, 12, 45, 0, tzinfo=timezone.utc)
    window_end = datetime(2000, 6, 29, 12, 55, 0, tzinfo=timezone.utc)

    result = refine_tca("A", LINE1, LINE2, "B", LINE1, LINE2, window_start, window_end)

    assert result.converged is True
    assert result.refinement_status == "ok"
    assert result.miss_distance_km == pytest.approx(0.0, abs=1e-3)
    assert result.relative_velocity_km_s == pytest.approx(0.0, abs=1e-6)