from datetime import datetime, timezone

from backend.orbital.tle import parse_tle

# Official Vallado SGP4 verification test vector (satellite 00005, 58002B)
VALID_LINE1 = "1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753"
VALID_LINE2 = "2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667"


def test_parse_valid_tle():
    result = parse_tle(VALID_LINE1, VALID_LINE2)

    assert result.is_valid is True
    assert result.validation_status == "valid"
    assert result.norad_id == "00005"
    assert result.classification == "U"


def test_parse_valid_tle_epoch():
    result = parse_tle(VALID_LINE1, VALID_LINE2)

    # Epoch string 00179.78495062 -> day 179 of year 2000
    assert result.epoch_utc.year == 2000
    assert result.epoch_utc.month == 6
    assert result.epoch_utc.day == 27
    assert result.epoch_utc.tzinfo == timezone.utc


def test_parse_tle_bad_checksum():
    # Deliberately corrupt the last digit of line1's checksum
    bad_line1 = VALID_LINE1[:-1] + "9"

    result = parse_tle(bad_line1, VALID_LINE2)

    assert result.is_valid is False
    assert result.validation_status == "checksum_failed"


def test_parse_tle_malformed_prefix():
    result = parse_tle("garbage line", VALID_LINE2)

    assert result.is_valid is False
    assert result.validation_status == "malformed_line_prefix"