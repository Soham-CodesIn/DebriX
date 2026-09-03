import os
import sys

import streamlit as st
import pandas as pd
from datetime import datetime


# Make the DebriX project root importable when Streamlit
# executes this page directly.
PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from frontend.api import (
    get_alerts,
    get_conjunctions,
    get_objects,
)

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="DebriX | Collision Alerts",
    page_icon="⚠️",
    layout="wide",
)


# ============================================================
# STYLING
# ============================================================

st.markdown(
    """
    <style>
        .alert-card {
            padding: 22px;
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.10);
            background: rgba(20,25,35,0.85);
            margin-bottom: 16px;
        }

        .alert-header {
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 6px;
        }

        .object-line {
            font-size: 17px;
            font-weight: 600;
            margin-bottom: 14px;
        }

        .muted {
            color: #9aa4b2;
            font-size: 14px;
        }

        .metric-box {
            padding: 16px;
            border-radius: 12px;
            background: rgba(30,40,55,0.75);
            border: 1px solid rgba(255,255,255,0.08);
        }

        .metric-label {
            color: #9aa4b2;
            font-size: 13px;
        }

        .metric-value {
            font-size: 24px;
            font-weight: 700;
        }

        .low-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            background: rgba(70,130,180,0.18);
            color: #66b3ff;
            font-weight: 700;
            font-size: 13px;
        }

        .medium-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            background: rgba(255,193,7,0.18);
            color: #ffc107;
            font-weight: 700;
            font-size: 13px;
        }

        .high-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            background: rgba(255,140,0,0.18);
            color: #ff9f43;
            font-weight: 700;
            font-size: 13px;
        }

        .critical-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            background: rgba(255,60,60,0.18);
            color: #ff6b6b;
            font-weight: 700;
            font-size: 13px;
        }

        .monitoring-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            background: rgba(70,130,180,0.18);
            color: #66b3ff;
            font-weight: 700;
            font-size: 13px;
        }

        .reason-box {
            padding: 14px 16px;
            border-radius: 10px;
            background: rgba(255,255,255,0.035);
            margin-top: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data(ttl=30)
def load_alerts():
    return get_alerts()


@st.cache_data(ttl=30)
def load_conjunctions():
    return get_conjunctions()


@st.cache_data(ttl=30)
def load_objects():
    return get_objects()


try:
    alerts_response = load_alerts()
    conjunctions_response = load_conjunctions()
    objects_response = load_objects()

except Exception as e:
    st.error(f"Unable to connect to the DebriX backend: {e}")
    st.stop()


# ============================================================
# NORMALIZE API RESPONSES
# ============================================================

def unwrap_list(data):
    """
    Backend currently returns:
        {"value": [...], "Count": N}

    This helper also supports a plain list.
    """
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        value = data.get("value")

        if isinstance(value, list):
            return value

    return []


alerts = unwrap_list(alerts_response)
conjunctions = unwrap_list(conjunctions_response)
objects = unwrap_list(objects_response)


# ============================================================
# OBJECT LOOKUP
# ============================================================

object_lookup = {}

for obj in objects:
    object_id = str(obj.get("object_id", ""))

    if not object_id:
        continue

    object_lookup[object_id] = obj.get(
        "name",
        f"Object {object_id}"
    )


def object_name(object_id):
    object_id = str(object_id)
    return object_lookup.get(
        object_id,
        f"Object {object_id}"
    )


# ============================================================
# CONJUNCTION LOOKUP
# ============================================================

conjunction_lookup = {}

for conjunction in conjunctions:
    conjunction_id = conjunction.get("conjunction_id")

    if conjunction_id:
        conjunction_lookup[str(conjunction_id)] = conjunction


# ============================================================
# BUILD DISPLAY EVENTS
# ============================================================

events = []


# ------------------------------------------------------------
# REAL ALERTS
# ------------------------------------------------------------

for alert in alerts:

    conjunction_id = str(
        alert.get("conjunction_id", "")
    )

    conjunction = conjunction_lookup.get(
        conjunction_id,
        {}
    )

    risk = conjunction.get(
        "risk_assessment",
        {}
    ) or {}

    object_a = str(
        conjunction.get(
            "object_a",
            alert.get("object_a", "")
        )
    )

    object_b = str(
        conjunction.get(
            "object_b",
            alert.get("object_b", "")
        )
    )

    severity = str(
        alert.get(
            "severity",
            risk.get("risk_level", "LOW")
        )
    ).upper()

    events.append(
        {
            "event_type": "ALERT",
            "alert_id": alert.get("alert_id"),
            "conjunction_id": conjunction_id,
            "object_a": object_a,
            "object_b": object_b,
            "object_a_name": object_name(object_a),
            "object_b_name": object_name(object_b),
            "severity": severity,
            "status": str(
                alert.get(
                    "status",
                    "OPEN"
                )
            ).upper(),
            "tca": conjunction.get("tca"),
            "miss_distance_km": conjunction.get(
                "miss_distance_km"
            ),
            "relative_velocity_km_s": conjunction.get(
                "relative_velocity_km_s"
            ),
            "risk_level": str(
                risk.get(
                    "risk_level",
                    severity
                )
            ).upper(),
            "confidence": risk.get(
                "confidence"
            ),
            "f_value": risk.get(
                "f_value"
            ),
            "pc": risk.get(
                "pc"
            ),
            "pc_status": risk.get(
                "pc_status"
            ),
            "methodology_version": risk.get(
                "methodology_version"
            ),
        }
    )


# ------------------------------------------------------------
# REAL CONJUNCTIONS WITHOUT ALERTS
#
# These are genuine conjunction events from the backend.
# They are displayed as MONITORING events rather than
# pretending they are elevated-risk alerts.
# ------------------------------------------------------------

alert_conjunction_ids = {
    str(event["conjunction_id"])
    for event in events
    if event.get("conjunction_id")
}


for conjunction in conjunctions:

    conjunction_id = str(
        conjunction.get(
            "conjunction_id",
            ""
        )
    )

    if not conjunction_id:
        continue

    if conjunction_id in alert_conjunction_ids:
        continue

    risk = conjunction.get(
        "risk_assessment",
        {}
    ) or {}

    object_a = str(
        conjunction.get(
            "object_a",
            ""
        )
    )

    object_b = str(
        conjunction.get(
            "object_b",
            ""
        )
    )

    risk_level = str(
        risk.get(
            "risk_level",
            "LOW"
        )
    ).upper()

    events.append(
        {
            "event_type": "MONITORING",
            "alert_id": None,
            "conjunction_id": conjunction_id,
            "object_a": object_a,
            "object_b": object_b,
            "object_a_name": object_name(object_a),
            "object_b_name": object_name(object_b),
            "severity": risk_level,
            "status": "MONITORING",
            "tca": conjunction.get("tca"),
            "miss_distance_km": conjunction.get(
                "miss_distance_km"
            ),
            "relative_velocity_km_s": conjunction.get(
                "relative_velocity_km_s"
            ),
            "risk_level": risk_level,
            "confidence": risk.get(
                "confidence"
            ),
            "f_value": risk.get(
                "f_value"
            ),
            "pc": risk.get(
                "pc"
            ),
            "pc_status": risk.get(
                "pc_status"
            ),
            "methodology_version": risk.get(
                "methodology_version"
            ),
        }
    )


# ============================================================
# PAGE HEADER
# ============================================================

st.markdown(
    """
    <h1 style="text-align:center; font-size:48px;">
        ⚠️ Collision Risk Alerts
    </h1>
    """,
    unsafe_allow_html=True,
)

if alerts:
    st.markdown(
        "Real collision-risk alerts generated from the DebriX backend."
    )
else:
    st.markdown(
        "No elevated-risk alerts are currently active. "
        "Showing real conjunction events under monitoring."
    )


st.divider()


# ============================================================
# EMPTY STATE
# ============================================================

if not events:

    st.info(
        "No conjunction or collision-risk events are currently available."
    )

    st.stop()


# ============================================================
# SUMMARY
# ============================================================

critical_count = sum(
    1 for event in events
    if event["severity"] == "CRITICAL"
)

high_count = sum(
    1 for event in events
    if event["severity"] == "HIGH"
)

medium_count = sum(
    1 for event in events
    if event["severity"] == "MEDIUM"
)

monitoring_count = sum(
    1 for event in events
    if event["event_type"] == "MONITORING"
)


# Find future TCAs
now = pd.Timestamp.utcnow()

if now.tzinfo is not None:
    now = now.tz_localize(None)


future_tcas = []

for event in events:

    tca_value = event.get("tca")

    if not tca_value:
        continue

    try:
        tca = pd.Timestamp(tca_value)

        if tca.tzinfo is not None:
            tca = tca.tz_localize(None)

        if tca > now:
            future_tcas.append(tca)

    except Exception:
        continue


if future_tcas:
    next_tca = min(future_tcas)
    hours_until_tca = (
        next_tca - now
    ).total_seconds() / 3600
else:
    next_tca = None
    hours_until_tca = None


c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Total Events",
        len(events)
    )

with c2:
    st.metric(
        "Critical Alerts",
        critical_count
    )

with c3:
    st.metric(
        "High-Risk Events",
        high_count
    )

with c4:

    if hours_until_tca is not None:
        if hours_until_tca < 1:
            value = f"{hours_until_tca * 60:.0f} min"
        else:
            value = f"{hours_until_tca:.1f} h"
    else:
        value = "—"

    st.metric(
        "Next TCA",
        value
    )


st.divider()


# ============================================================
# FILTERS
# ============================================================

st.subheader("Event Filters")

f1, f2, f3, f4 = st.columns(4)

with f1:
    search = st.text_input(
        "Search",
        placeholder="Object name or conjunction ID..."
    )

with f2:
    severity_filter = st.multiselect(
        "Risk Level",
        ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        default=[]
    )

with f3:
    event_filter = st.selectbox(
        "Event Type",
        [
            "All",
            "Alerts Only",
            "Monitoring Only",
        ]
    )

with f4:
    sort_option = st.selectbox(
        "Sort By",
        [
            "Next TCA — soonest first",
            "TCA",
            "Miss Distance",
            "Risk Level",
            "F-value",
        ]
    )


# ============================================================
# FILTER DATA
# ============================================================

filtered_events = events.copy()


if search:

    query = search.lower()

    filtered_events = [
        event
        for event in filtered_events
        if (
            query in str(
                event.get("conjunction_id", "")
            ).lower()
            or query in str(
                event.get("object_a_name", "")
            ).lower()
            or query in str(
                event.get("object_b_name", "")
            ).lower()
            or query in str(
                event.get("object_a", "")
            ).lower()
            or query in str(
                event.get("object_b", "")
            ).lower()
        )
    ]


if severity_filter:

    filtered_events = [
        event
        for event in filtered_events
        if event["severity"] in severity_filter
    ]


if event_filter == "Alerts Only":

    filtered_events = [
        event
        for event in filtered_events
        if event["event_type"] == "ALERT"
    ]

elif event_filter == "Monitoring Only":

    filtered_events = [
        event
        for event in filtered_events
        if event["event_type"] == "MONITORING"
    ]


# ============================================================
# SORTING
# ============================================================

severity_order = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
}


if sort_option == "Next TCA — soonest first":

    now_utc = pd.Timestamp.now(tz="UTC")

    future_events = []
    past_events = []
    no_tca_events = []

    for event in filtered_events:
        try:
            tca = pd.Timestamp(event.get("tca"))
            if tca.tzinfo is None:
                tca = tca.tz_localize("UTC")
            else:
                tca = tca.tz_convert("UTC")
        except Exception:
            tca = pd.NaT

        if pd.isna(tca):
            no_tca_events.append(event)
        elif tca >= now_utc:
            future_events.append((tca, event))
        else:
            past_events.append((tca, event))

    future_events.sort(key=lambda item: item[0])
    past_events.sort(key=lambda item: item[0], reverse=True)

    filtered_events = (
        [event for _, event in future_events]
        + [event for _, event in past_events]
        + no_tca_events
    )

elif sort_option == "Risk Level":

    filtered_events.sort(
        key=lambda x: severity_order.get(
            x["severity"],
            99
        )
    )

elif sort_option == "Miss Distance":

    filtered_events.sort(
        key=lambda x: (
            x["miss_distance_km"]
            if x["miss_distance_km"] is not None
            else float("inf")
        )
    )

elif sort_option == "F-value":

    filtered_events.sort(
        key=lambda x: (
            x["f_value"]
            if x["f_value"] is not None
            else -1
        ),
        reverse=True
    )

else:

    def tca_sort(event):
        try:
            return pd.Timestamp(
                event["tca"]
            )
        except Exception:
            return pd.Timestamp.max

    filtered_events.sort(
        key=tca_sort
    )


st.caption(
    f"Showing {len(filtered_events)} of {len(events)} events"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def format_number(value, decimals=2):

    if value is None:
        return "Unavailable"

    try:
        return f"{float(value):.{decimals}f}"
    except Exception:
        return str(value)


def format_tca(value):

    if not value:
        return "Unavailable"

    try:
        timestamp = pd.Timestamp(value)

        return timestamp.strftime(
            "%d %b %Y • %H:%M:%S UTC"
        )

    except Exception:
        return str(value)


def risk_badge(level):

    level = str(level).upper()

    css_class = {
        "CRITICAL": "critical-badge",
        "HIGH": "high-badge",
        "MEDIUM": "medium-badge",
        "LOW": "low-badge",
    }.get(
        level,
        "low-badge"
    )

    return (
        f'<span class="{css_class}">'
        f'{level}'
        f'</span>'
    )


# ============================================================
# EVENT CARDS
# ============================================================

for index, event in enumerate(filtered_events):

    severity = event["severity"]

    event_type = event["event_type"]

    if event_type == "ALERT":
        type_label = "ACTIVE ALERT"
    else:
        type_label = "MONITORING"

    st.markdown(
        '<div class="alert-card">',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    h1, h2 = st.columns([4, 1])

    with h1:

        st.markdown(
            f"""
            <div class="alert-header">
                {event["object_a_name"]}
                ↔
                {event["object_b_name"]}
            </div>

            <div class="muted">
                Conjunction ID:
                {event["conjunction_id"]}
            </div>
            """,
            unsafe_allow_html=True
        )

    with h2:

        st.markdown(
            risk_badge(severity),
            unsafe_allow_html=True
        )

        st.caption(type_label)


    st.markdown("")


    # --------------------------------------------------------
    # PRIMARY METRICS
    # --------------------------------------------------------

    m1, m2, m3, m4 = st.columns(4)

    with m1:

        st.markdown(
            '<div class="metric-box">',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="metric-label">Miss Distance</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f'<div class="metric-value">'
            f'{format_number(event["miss_distance_km"])} km'
            f'</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    with m2:

        st.markdown(
            '<div class="metric-box">',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="metric-label">'
            'Relative Velocity'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f'<div class="metric-value">'
            f'{format_number(event["relative_velocity_km_s"])} km/s'
            f'</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    with m3:

        st.markdown(
            '<div class="metric-box">',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="metric-label">F-value</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f'<div class="metric-value">'
            f'{format_number(event["f_value"], 3)}'
            f'</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    with m4:

        st.markdown(
            '<div class="metric-box">',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="metric-label">Confidence</div>',
            unsafe_allow_html=True
        )

        confidence = event.get(
            "confidence"
        )

        st.markdown(
            f'<div class="metric-value">'
            f'{str(confidence).upper() if confidence else "—"}'
            f'</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )


    st.markdown("")


    # --------------------------------------------------------
    # TCA
    # --------------------------------------------------------

    st.markdown(
        f"""
        **Time of Closest Approach**

        `{format_tca(event["tca"])}`
        """
    )


    # --------------------------------------------------------
    # RISK ASSESSMENT
    # --------------------------------------------------------

    with st.expander(
        "Risk Assessment Details",
        expanded=False
    ):

        r1, r2 = st.columns(2)

        with r1:

            st.markdown(
                f"""
                **Risk Level:** {event["risk_level"]}

                **Confidence:** {
                    str(event["confidence"]).upper()
                    if event["confidence"]
                    else "Unavailable"
                }

                **F-value:** {
                    format_number(
                        event["f_value"],
                        6
                    )
                }
                """
            )

        with r2:

            pc = event.get("pc")

            if pc is None:

                pc_text = "Unavailable"

            else:

                pc_text = f"{pc:.6e}"

            st.markdown(
                f"""
                **Probability of Collision (Pc):** {pc_text}

                **Pc Status:** {
                    event["pc_status"]
                    if event["pc_status"]
                    else "Unavailable"
                }

                **Methodology:** {
                    event["methodology_version"]
                    if event["methodology_version"]
                    else "Unavailable"
                }
                """
            )


        st.markdown(
            '<div class="reason-box">',
            unsafe_allow_html=True
        )

        if event["pc"] is None:

            st.markdown(
                """
                **Why Pc is unavailable**

                The current orbital dataset does not contain
                covariance information for these objects.
                Therefore DebriX cannot calculate a
                statistically valid probability of collision.

                The event is instead assessed using the
                deterministic risk features available from
                the conjunction analysis.
                """
            )

        else:

            st.markdown(
                """
                Probability-of-collision data is available
                and can be incorporated into the risk assessment.
                """
            )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )


    # --------------------------------------------------------
    # TECHNICAL DETAILS
    # --------------------------------------------------------

    with st.expander(
        "Technical Details",
        expanded=False
    ):

        t1, t2 = st.columns(2)

        with t1:

            st.markdown(
                f"""
                **Object A**

                {event["object_a_name"]}
                (`{event["object_a"]}`)

                **Object B**

                {event["object_b_name"]}
                (`{event["object_b"]}`)
                """
            )

        with t2:

            st.markdown(
                f"""
                **Event Type**

                {type_label}

                **Status**

                {event["status"]}

                **Conjunction ID**

                `{event["conjunction_id"]}`
                """
            )


    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "DebriX • Collision monitoring powered by real orbital "
    "tracking and conjunction-analysis data."
)