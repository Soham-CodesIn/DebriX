def _tle_checksum(line: str) -> int:
    total = 0
    for char in line[:-1]:
        if char.isdigit():
            total += int(char)
        elif char == "-":
            total += 1
    return total % 10


def _validate_line_checksum(line: str) -> bool:
    if len(line) < 1:
        return False
    expected = int(line[-1])
    return _tle_checksum(line) == expected

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class ParsedTLE:
    norad_id: str
    classification: str
    epoch_utc: datetime
    line1: str
    line2: str
    is_valid: bool
    validation_status: str


def _parse_epoch(epoch_str: str) -> datetime:
    # epoch_str format: YYDDD.DDDDDDDD (2-digit year + day-of-year fraction)
    year_two_digit = int(epoch_str[:2])
    day_fraction = float(epoch_str[2:])
    year = 2000 + year_two_digit if year_two_digit < 57 else 1900 + year_two_digit

    day_of_year = int(day_fraction)
    fractional_day = day_fraction - day_of_year

    dt = datetime(year, 1, 1, tzinfo=timezone.utc)
    dt = dt.replace(day=1)
    from datetime import timedelta
    dt = datetime(year, 1, 1, tzinfo=timezone.utc) + timedelta(days=day_of_year - 1)
    dt = dt + timedelta(days=fractional_day)
    return dt


def parse_tle(line1: str, line2: str) -> ParsedTLE:
    line1 = line1.rstrip("\n")
    line2 = line2.rstrip("\n")

    if not line1.startswith("1 ") or not line2.startswith("2 "):
        return ParsedTLE(
            norad_id="", classification="", epoch_utc=None,
            line1=line1, line2=line2,
            is_valid=False, validation_status="malformed_line_prefix",
        )

    if not _validate_line_checksum(line1) or not _validate_line_checksum(line2):
        return ParsedTLE(
            norad_id="", classification="", epoch_utc=None,
            line1=line1, line2=line2,
            is_valid=False, validation_status="checksum_failed",
        )

    norad_id = line1[2:7].strip()
    classification = line1[7]
    epoch_str = line1[18:32].strip()

    try:
        epoch_utc = _parse_epoch(epoch_str)
    except (ValueError, IndexError):
        return ParsedTLE(
            norad_id=norad_id, classification=classification, epoch_utc=None,
            line1=line1, line2=line2,
            is_valid=False, validation_status="epoch_parse_failed",
        )

    return ParsedTLE(
        norad_id=norad_id,
        classification=classification,
        epoch_utc=epoch_utc,
        line1=line1,
        line2=line2,
        is_valid=True,
        validation_status="valid",
    )