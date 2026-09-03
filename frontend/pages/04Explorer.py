import os
import sys

import streamlit as st
import pandas as pd


# ============================================================
# IMPORT PATH
# ============================================================

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
    get_conjunctions,
    get_objects,
    get_propagation,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="DebriX | Conjunction Explorer",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# STYLING
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background: transparent;
    }

    .object-card {
        padding: 22px;
        border-radius: 14px;
        background: rgba(20,25,35,0.82);
        border: 1px solid rgba(255,255,255,0.10);
        margin-bottom: 18px;
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

    .risk-low {
        color: #66b3ff;
        font-weight: 700;
    }

    .risk-medium {
        color: #ffc107;
        font-weight: 700;
    }

    .risk-high {
        color: #ff9f43;
        font-weight: 700;
    }

    .risk-critical {
        color: #ff6b6b;
        font-weight: 700;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data(ttl=30)
def load_conjunctions():
    return get_conjunctions()


@st.cache_data(ttl=30)
def load_objects():
    return get_objects()


try:

    conjunction_response = load_conjunctions()
    object_response = load_objects()

except Exception as e:

    st.error(
        f"Unable to connect to the DebriX backend: {e}"
    )

    st.stop()


# ============================================================
# API RESPONSE HELPER
# ============================================================

def unwrap_list(data):

    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        value = data.get("value")

        if isinstance(value, list):
            return value

    return []


conjunctions = unwrap_list(
    conjunction_response
)

objects = unwrap_list(
    object_response
)


# ============================================================
# OBJECT LOOKUP
# ============================================================

object_lookup = {}

for obj in objects:

    object_id = str(
        obj.get("object_id", "")
    )

    if not object_id:
        continue

    object_lookup[object_id] = {
        "name": obj.get(
            "name",
            f"Object {object_id}"
        ),
        "type": obj.get(
            "object_type",
            "Unknown"
        ),
        "created_at": obj.get(
            "created_at"
        ),
    }


def get_object_name(object_id):

    object_id = str(object_id)

    if object_id in object_lookup:

        return object_lookup[
            object_id
        ]["name"]

    return f"Object {object_id}"


# ============================================================
# NORMALIZE CONJUNCTION DATA
# ============================================================

records = []

for conjunction in conjunctions:

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

    records.append(
        {
            "conjunction_id":
                conjunction.get(
                    "conjunction_id"
                ),

            "object_a_id":
                object_a,

            "object_a_name":
                get_object_name(object_a),

            "object_b_id":
                object_b,

            "object_b_name":
                get_object_name(object_b),

            "tca":
                conjunction.get(
                    "tca"
                ),

            "miss_distance_km":
                conjunction.get(
                    "miss_distance_km"
                ),

            "relative_velocity_km_s":
                conjunction.get(
                    "relative_velocity_km_s"
                ),

            "risk_level":
                str(
                    risk.get(
                        "risk_level",
                        "LOW"
                    )
                ).upper(),

            "confidence":
                risk.get(
                    "confidence"
                ),

            "f_value":
                risk.get(
                    "f_value"
                ),

            "pc":
                risk.get(
                    "pc"
                ),

            "pc_status":
                risk.get(
                    "pc_status"
                ),

            "methodology_version":
                risk.get(
                    "methodology_version"
                ),
        }
    )


df = pd.DataFrame(records)


# ============================================================
# HEADER
# ============================================================

st.title("🔎 Conjunction Explorer")

st.markdown(
    """
    Search, filter and inspect real orbital conjunction
    events detected by the DebriX analysis pipeline.
    """
)

st.divider()


# ============================================================
# EMPTY DATA CHECK
# ============================================================

if df.empty:

    st.info(
        "No conjunction events are currently available."
    )

    st.stop()


# ============================================================
# SUMMARY METRICS
# ============================================================

total_events = len(df)

high_events = len(
    df[
        df["risk_level"].isin(
            ["HIGH", "CRITICAL"]
        )
    ]
)

medium_events = len(
    df[
        df["risk_level"] == "MEDIUM"
    ]
)

low_events = len(
    df[
        df["risk_level"] == "LOW"
    ]
)

avg_miss_distance = df[
    "miss_distance_km"
].mean()


m1, m2, m3, m4 = st.columns(4)


with m1:

    st.metric(
        "Conjunction Events",
        total_events
    )


with m2:

    st.metric(
        "High / Critical",
        high_events
    )


with m3:

    st.metric(
        "Medium Risk",
        medium_events
    )


with m4:

    if pd.notna(avg_miss_distance):

        value = (
            f"{avg_miss_distance:.2f} km"
        )

    else:

        value = "—"

    st.metric(
        "Average Miss Distance",
        value
    )


st.divider()


# ============================================================
# SEARCH + FILTERS
# ============================================================

st.subheader(
    "Search & Screening"
)


f1, f2, f3 = st.columns(
    [2, 1, 1]
)


with f1:

    search_query = st.text_input(
        "Search",
        placeholder=(
            "Object name, object ID, "
            "or conjunction ID..."
        )
    )


with f2:

    risk_options = [
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW",
    ]

    selected_risk = st.multiselect(
        "Risk Level",
        risk_options,
        default=risk_options,
    )


with f3:

    confidence_options = [
        "HIGH",
        "MEDIUM",
        "LOW",
    ]

    selected_confidence = st.multiselect(
        "Confidence",
        confidence_options,
        default=confidence_options,
    )


# ============================================================
# NUMERIC FILTERS
# ============================================================

n1, n2 = st.columns(2)


max_distance_available = float(
    df["miss_distance_km"]
    .dropna()
    .max()
)

if max_distance_available <= 0:
    max_distance_available = 100.0


with n1:

    max_miss_distance = st.slider(
        "Maximum Miss Distance (km)",
        min_value=0.0,
        max_value=max(
            100.0,
            round(
                max_distance_available + 5,
                0
            )
        ),
        value=max(
            100.0,
            round(
                max_distance_available + 5,
                0
            )
        ),
        step=1.0,
    )


with n2:

    sort_by = st.selectbox(
        "Sort Results By",
        [
            "Next TCA — soonest first",
            "Miss distance — closest first",
            "Risk — highest first",
            "Relative velocity — highest first",
            "F-value — highest first",
        ],
    )


# ============================================================
# APPLY FILTERS
# ============================================================

filtered = df.copy()


if search_query:

    query = search_query.lower()

    searchable = (
        filtered[
            [
                "conjunction_id",
                "object_a_id",
                "object_a_name",
                "object_b_id",
                "object_b_name",
            ]
        ]
        .fillna("")
        .astype(str)
        .apply(
            lambda column:
                column.str.lower()
                .str.contains(
                    query,
                    regex=False
                )
        )
        .any(axis=1)
    )

    filtered = filtered[
        searchable
    ]


if selected_risk:

    filtered = filtered[
        filtered["risk_level"].isin(
            selected_risk
        )
    ]

else:

    filtered = filtered.iloc[0:0]


if selected_confidence:

    confidence_upper = (
        filtered["confidence"]
        .fillna("")
        .astype(str)
        .str.upper()
    )

    filtered = filtered[
        confidence_upper.isin(
            selected_confidence
        )
    ]

else:

    filtered = filtered.iloc[0:0]


filtered = filtered[
    (
        filtered[
            "miss_distance_km"
        ]
        .fillna(float("inf"))
        <= max_miss_distance
    )
]


# ============================================================
# SORT
# ============================================================

if sort_by == "Next TCA — soonest first":

    now_utc = pd.Timestamp.now(tz="UTC")

    filtered["_tca_parsed"] = pd.to_datetime(
        filtered["tca"],
        errors="coerce",
        utc=True
    )

    future = filtered[
        filtered["_tca_parsed"] >= now_utc
    ].copy()

    past = filtered[
        filtered["_tca_parsed"] < now_utc
    ].copy()

    no_tca = filtered[
        filtered["_tca_parsed"].isna()
    ].copy()

    future = future.sort_values(
        "_tca_parsed",
        ascending=True
    )

    past = past.sort_values(
        "_tca_parsed",
        ascending=False
    )

    filtered = pd.concat(
        [future, past, no_tca],
        ignore_index=True
    )

elif sort_by == "Miss distance — closest first":

    filtered = filtered.sort_values(
        "miss_distance_km",
        ascending=True,
        na_position="last"
    )

elif sort_by == "Risk — highest first":

    risk_order = {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3,
    }

    filtered["_sort"] = (
        filtered["risk_level"]
        .map(risk_order)
        .fillna(99)
    )

    filtered = filtered.sort_values(
        "_sort"
    )

elif sort_by == "Relative velocity — highest first":

    filtered = filtered.sort_values(
        "relative_velocity_km_s",
        ascending=False,
        na_position="last"
    )

elif sort_by == "F-value — highest first":

    filtered = filtered.sort_values(
        "f_value",
        ascending=False,
        na_position="last"
    )


# ============================================================
# RESULTS TABLE
# ============================================================

st.markdown("---")

st.subheader(
    "Conjunction Events"
)

st.caption(
    f"Showing {len(filtered)} "
    f"of {len(df)} real conjunction events."
)


if filtered.empty:

    st.info(
        "No conjunctions match the selected filters."
    )

else:

    display_df = filtered[
        [
            "conjunction_id",
            "object_a_name",
            "object_b_name",
            "tca",
            "miss_distance_km",
            "relative_velocity_km_s",
            "f_value",
            "risk_level",
            "confidence",
        ]
    ].copy()


    display_df.columns = [
        "Conjunction ID",
        "Object A",
        "Object B",
        "TCA (UTC)",
        "Miss Distance (km)",
        "Relative Velocity (km/s)",
        "F-value",
        "Risk",
        "Confidence",
    ]


    display_df["TCA (UTC)"] = pd.to_datetime(
        display_df["TCA (UTC)"],
        errors="coerce"
    )


    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "TCA (UTC)": st.column_config.DatetimeColumn(
                format="YYYY-MM-DD HH:mm:ss"
            ),

            "Miss Distance (km)": st.column_config.NumberColumn(
                format="%.2f"
            ),

            "Relative Velocity (km/s)": st.column_config.NumberColumn(
                format="%.2f"
            ),

            "F-value": st.column_config.NumberColumn(
                format="%.4f"
            ),
        },
    )


# ============================================================
# DETAIL INSPECTION
# ============================================================

st.divider()

st.subheader(
    "📄 Conjunction Detail"
)


if filtered.empty:

    st.info(
        "Apply less restrictive filters to inspect an event."
    )

else:

    event_ids = (
        filtered[
            "conjunction_id"
        ]
        .astype(str)
        .tolist()
    )


    selected_id = st.selectbox(
        "Select a conjunction to inspect",
        event_ids,
    )


    event = filtered[
        filtered[
            "conjunction_id"
        ].astype(str)
        == selected_id
    ].iloc[0]


    # --------------------------------------------------------
    # OBJECT INFORMATION
    # --------------------------------------------------------

    st.markdown(
        '<div class="object-card">',
        unsafe_allow_html=True
    )


    object_a_type = object_lookup.get(
        str(event["object_a_id"]),
        {}
    ).get(
        "type",
        "Unknown"
    )


    object_b_type = object_lookup.get(
        str(event["object_b_id"]),
        {}
    ).get(
        "type",
        "Unknown"
    )


    st.markdown(
        f"""
        ### 🛰️ {event["object_a_name"]}

        **Object ID:** `{event["object_a_id"]}`

        **Object Type:** `{object_a_type}`

        ---

        ### 🛰️ {event["object_b_name"]}

        **Object ID:** `{event["object_b_id"]}`

        **Object Type:** `{object_b_type}`
        """
    )


    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


    # --------------------------------------------------------
    # EVENT METRICS
    # --------------------------------------------------------

    d1, d2, d3, d4 = st.columns(4)


    with d1:

        if pd.notna(
            event["miss_distance_km"]
        ):

            value = (
                f'{event["miss_distance_km"]:.2f} km'
            )

        else:

            value = "Unavailable"


        st.metric(
            "Miss Distance",
            value
        )


    with d2:

        if pd.notna(
            event[
                "relative_velocity_km_s"
            ]
        ):

            value = (
                f'{event["relative_velocity_km_s"]:.2f} km/s'
            )

        else:

            value = "Unavailable"


        st.metric(
            "Relative Velocity",
            value
        )


    with d3:

        if pd.notna(
            event["f_value"]
        ):

            value = (
                f'{event["f_value"]:.4f}'
            )

        else:

            value = "Unavailable"


        st.metric(
            "F-value",
            value
        )


    with d4:

        st.metric(
            "Risk Level",
            event["risk_level"]
        )


    # --------------------------------------------------------
    # TCA
    # --------------------------------------------------------

    st.markdown(
        "### ⏱️ Time of Closest Approach"
    )


    try:

        tca = pd.Timestamp(
            event["tca"]
        )

        st.info(
            tca.strftime(
                "%d %B %Y • %H:%M:%S UTC"
            )
        )

    except Exception:

        st.info(
            "TCA unavailable"
        )


    # --------------------------------------------------------
    # RISK ASSESSMENT
    # --------------------------------------------------------

    with st.expander(
        "🛡️ Risk Assessment",
        expanded=True
    ):

        r1, r2 = st.columns(2)


        with r1:

            st.write(
                "**Risk Level:**",
                event["risk_level"]
            )

            confidence = event[
                "confidence"
            ]

            if pd.notna(confidence):

                confidence_text = str(
                    confidence
                ).upper()

            else:

                confidence_text = (
                    "Unavailable"
                )


            st.write(
                "**Confidence:**",
                confidence_text
            )


            if pd.notna(
                event["f_value"]
            ):

                f_value_text = (
                    f'{event["f_value"]:.6f}'
                )

            else:

                f_value_text = (
                    "Unavailable"
                )


            st.write(
                "**F-value:**",
                f_value_text
            )


        with r2:

            pc = event["pc"]


            if pd.isna(pc):

                pc_text = "Unavailable"

            else:

                pc_text = (
                    f"{pc:.6e}"
                )


            st.write(
                "**Probability of Collision (Pc):**",
                pc_text
            )


            pc_status = event[
                "pc_status"
            ]

            st.write(
                "**Pc Status:**",
                pc_status
                if pd.notna(pc_status)
                else "Unavailable"
            )


            methodology = event[
                "methodology_version"
            ]

            st.write(
                "**Methodology:**",
                methodology
                if pd.notna(methodology)
                else "Unavailable"
            )


        if pd.isna(pc):

            st.warning(
                "Probability of collision is unavailable "
                "because covariance data is not currently "
                "available for this conjunction."
            )


    # --------------------------------------------------------
    # OBJECT PROPAGATION
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "🛰️ Current Orbital State"
    )


    selected_object = st.radio(
        "Inspect object",
        [
            event["object_a_name"],
            event["object_b_name"],
        ],
        horizontal=True,
    )


    if selected_object == event[
        "object_a_name"
    ]:

        selected_object_id = (
            event["object_a_id"]
        )

    else:

        selected_object_id = (
            event["object_b_id"]
        )


    if st.button(
        "Load Latest Propagation State",
        key=f"prop_{selected_id}_{selected_object_id}"
    ):

        try:

            propagation = get_propagation(
                selected_object_id
            )

            if propagation:

                st.json(
                    propagation
                )

            else:

                st.info(
                    "No stored propagation state "
                    "is available for this object."
                )

        except Exception as e:

            st.error(
                f"Unable to load propagation state: {e}"
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "DebriX • Explorer powered by real orbital "
    "tracking, SGP4 propagation and conjunction analysis."
)