import os

import pytest
from dotenv import load_dotenv

from backend.services.spacetrack import fetch_gp_data

load_dotenv()

SPACETRACK_USER = os.environ.get("SPACETRACK_USER")
SPACETRACK_PASS = os.environ.get("SPACETRACK_PASS")

requires_credentials = pytest.mark.skipif(
    not SPACETRACK_USER or not SPACETRACK_PASS,
    reason="SPACETRACK_USER/SPACETRACK_PASS not set in .env — skipping live network test",
)


@requires_credentials
def test_fetch_gp_data_for_iss():
    # NORAD ID 25544 = ISS, a stable/known object to test against
    result = fetch_gp_data(SPACETRACK_USER, SPACETRACK_PASS, norad_ids=["25544"])

    assert result.status == "ok"
    assert result.success is True
    assert result.raw_records is not None
    assert len(result.raw_records) >= 1

    record = result.raw_records[0]
    assert record["NORAD_CAT_ID"] == "25544"
    assert "TLE_LINE1" in record
    assert "TLE_LINE2" in record


@requires_credentials
def test_fetch_gp_data_bad_credentials():
    result = fetch_gp_data("not_a_real_user", "not_a_real_password", norad_ids=["25544"])

    assert result.success is False
    assert result.status == "login_failed"