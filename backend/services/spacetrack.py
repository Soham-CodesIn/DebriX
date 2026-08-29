import requests
from dataclasses import dataclass

_LOGIN_URL = "https://www.space-track.org/ajaxauth/login"
_BASE_QUERY_URL = "https://www.space-track.org/basicspacedata/query"


@dataclass
class SpaceTrackFetchResult:
    success: bool
    status: str
    raw_records: list[dict] | None

def _login(session: requests.Session, username: str, password: str) -> bool:
    response = session.post(
        _LOGIN_URL,
        data={"identity": username, "password": password},
        timeout=30,
    )
    if response.status_code != 200:
        return False
    # Space-Track returns HTTP 200 even on bad credentials; the failure
    # only shows up in the response body text, not the status code.
    if "Login failed" in response.text or "FAIL" in response.text.upper():
        return False
    return True
def fetch_gp_data(username: str, password: str, norad_ids: list[str] | None = None,
                   limit: int = 100) -> SpaceTrackFetchResult:
    session = requests.Session()

    if not _login(session, username, password):
        return SpaceTrackFetchResult(
            success=False,
            status="login_failed",
            raw_records=None,
        )

    if norad_ids:
        norad_filter = ",".join(norad_ids)
        query_path = (
            f"class/gp/NORAD_CAT_ID/{norad_filter}/orderby/EPOCH desc/format/json"
        )
    else:
        query_path = (
            f"class/gp/decay_date/null-val/orderby/NORAD_CAT_ID/limit/{limit}/format/json"
        )

    response = session.get(f"{_BASE_QUERY_URL}/{query_path}", timeout=60)

    if response.status_code != 200:
        return SpaceTrackFetchResult(
            success=False,
            status=f"query_failed_http_{response.status_code}",
            raw_records=None,
        )

    try:
        records = response.json()
    except ValueError:
        return SpaceTrackFetchResult(
            success=False,
            status="invalid_json_response",
            raw_records=None,
        )

    return SpaceTrackFetchResult(
        success=True,
        status="ok",
        raw_records=records,
    )

