import streamlit as st  # type: ignore[import-not-found]
import pandas as pd  # type: ignore[import-not-found]
import plotly.express as px  # type: ignore[import-not-found]

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api import get_conjunctions


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    initial_sidebar_state="collapsed",
    layout="wide",
    page_title="DebriX Dashboard",
    page_icon="🛰️",
)


# ============================================================
# LOAD REAL BACKEND DATA
# ============================================================

@st.cache_data(ttl=30)
def load_dashboard_data():
    """
    Load conjunction data from the Flask backend.

    Flask endpoint:
        GET /conjunctions
    """

    conjunctions = get_conjunctions()

    if not conjunctions:
        return pd.DataFrame()

    rows = []

    for conjunction in conjunctions:

        risk = conjunction.get("risk_assessment") or {}

        rows.append({
            "conjunction_id": conjunction.get(
                "conjunction_id"
            ),

            "object_a": conjunction.get(
                "object_a"
            ),

            "object_b": conjunction.get(
                "object_b"
            ),

            "tca": conjunction.get(
                "tca"
            ),

            "miss_distance_km": conjunction.get(
                "miss_distance_km"
            ),

            "relative_velocity_km_s": conjunction.get(
                "relative_velocity_km_s"
            ),

            "risk_level": risk.get(
                "risk_level",
                "UNKNOWN"
            ),

            "confidence": risk.get(
                "confidence",
                "UNKNOWN"
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
        })

    df = pd.DataFrame(rows)

    df["tca"] = pd.to_datetime(
        df["tca"],
        errors="coerce"
    )

    df["risk_level"] = (
        df["risk_level"]
        .fillna("UNKNOWN")
        .astype(str)
        .str.upper()
    )

    df["confidence"] = (
        df["confidence"]
        .fillna("UNKNOWN")
        .astype(str)
        .str.upper()
    )

    return df


# ============================================================
# FETCH DATA
# ============================================================

try:
    df_events = load_dashboard_data()

except Exception as e:

    st.error(
        "Unable to connect to the DebriX backend."
    )

    st.code(str(e))

    st.stop()


# ============================================================
# HEADER
# ============================================================

st.title("🛰️ DebriX Command Dashboard")

st.header(
    "Monitor tracked objects, conjunction candidates, "
    "orbital-data freshness and collision-risk events."
)


# ============================================================
# CUSTOM STYLE
# ============================================================

st.markdown(
    """
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&display=swap'
    );

    .stApp {
        overflow: hidden;
        background: transparent;
    }

    h1 {
        text-align: center;
        font-family: 'Orbitron', sans-serif !important;
        font-size: 70px !important;
    }

    h2 {
        text-align: center;
        font-family: 'Orbitron', sans-serif !important;
        font-size: 25px !important;
        font-weight: 500 !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# BACKGROUND VIDEO
# ============================================================

video_url = (
    "https://www.pexels.com/download/video/10296173/"
)

st.markdown(
    f"""
    <style>

    #bg-video {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        object-fit: cover;
        z-index: -2;
    }}

    </style>

    <video id="bg-video" autoplay muted loop playsinline>
        <source src="{video_url}" type="video/mp4">
    </video>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# EMPTY DATABASE HANDLING
# ============================================================

if df_events.empty:

    st.warning(
        "No conjunction data is currently available "
        "in the DebriX database."
    )

    st.info(
        "Run the DebriX refresh pipeline to populate "
        "objects and conjunction results."
    )

    st.stop()


# ============================================================
# CALCULATE DASHBOARD METRICS
# ============================================================

screened_candidates = len(df_events)

high_risk_events = len(
    df_events[
        df_events["risk_level"] == "HIGH"
    ]
)

medium_risk_events = len(
    df_events[
        df_events["risk_level"] == "MEDIUM"
    ]
)

low_risk_events = len(
    df_events[
        df_events["risk_level"] == "LOW"
    ]
)

unknown_risk_events = len(
    df_events[
        df_events["risk_level"] == "UNKNOWN"
    ]
)


# ============================================================
# NEXT TCA
# ============================================================

future_events = df_events[
    df_events["tca"].notna()
]

if not future_events.empty:

    # Backend returns timezone-naive ISO timestamps.
    # Use a timezone-naive UTC timestamp for comparison.
    now = pd.Timestamp.utcnow().tz_localize(None)

    future_events = future_events[
        future_events["tca"] >= now
    ]

if not future_events.empty:

    next_event = (
        future_events
        .sort_values("tca")
        .iloc[0]
    )

    next_tca = next_event["tca"]

    now = pd.Timestamp.utcnow().tz_localize(None)

    hours_to_next_tca = (
        next_tca - now
    ).total_seconds() / 3600

else:

    next_event = (
        df_events
        .sort_values("tca")
        .iloc[0]
    )

    next_tca = next_event["tca"]

    hours_to_next_tca = None


# ============================================================
# KPI CARDS
# ============================================================

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)


with kpi1:

    st.metric(
        label="Tracked Conjunctions",
        value=f"{screened_candidates:,}"
    )


with kpi2:

    st.metric(
        label="High-Risk Events",
        value=f"{high_risk_events:,}"
    )


with kpi3:

    st.metric(
        label="Medium-Risk Events",
        value=f"{medium_risk_events:,}"
    )


with kpi4:

    if hours_to_next_tca is not None:

        st.metric(
            label="Next TCA",
            value=f"{hours_to_next_tca:.1f} h"
        )

    else:

        st.metric(
            label="Next TCA",
            value="—"
        )


with kpi5:

    valid_f_values = (
        pd.to_numeric(
            df_events["f_value"],
            errors="coerce"
        )
        .dropna()
    )

    if not valid_f_values.empty:

        avg_f_value = valid_f_values.mean()

        st.metric(
            label="Avg F-Value",
            value=f"{avg_f_value:.3f}"
        )

    else:

        st.metric(
            label="Avg F-Value",
            value="—"
        )


st.markdown("---")


# ============================================================
# SECTION 1 — RISK OVERVIEW
# ============================================================

st.subheader("📊 Risk Overview")

risk_col1, risk_col2 = st.columns(2)


# ============================================================
# RISK DISTRIBUTION DONUT
# ============================================================

with risk_col1:

    risk_counts = pd.DataFrame({
        "Risk Level": [
            "HIGH",
            "MEDIUM",
            "LOW",
            "UNKNOWN",
        ],

        "Count": [
            high_risk_events,
            medium_risk_events,
            low_risk_events,
            unknown_risk_events,
        ],
    })

    # Remove categories with zero events
    risk_counts = risk_counts[
        risk_counts["Count"] > 0
    ]

    fig_donut = px.pie(
        risk_counts,
        names="Risk Level",
        values="Count",
        hole=0.62,
        color="Risk Level",

        color_discrete_map={
            "HIGH": "#ff3b30",
            "MEDIUM": "#ffb000",
            "LOW": "#00d084",
            "UNKNOWN": "#808080",
        },
    )

    fig_donut.update_traces(
        textinfo="percent",

        hovertemplate=(
            "<b>%{label}</b><br>"
            "Events: %{value}<br>"
            "Share: %{percent}"
            "<extra></extra>"
        ),
    )

    fig_donut.update_layout(
        height=360,
        showlegend=True,

        legend=dict(
            orientation="h",
            y=-0.08,
        ),

        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(
        fig_donut,
        use_container_width=True,
    )


# ============================================================
# F-VALUE DISTRIBUTION
# ============================================================

with risk_col2:

    f_value_df = df_events.copy()

    f_value_df["f_value"] = pd.to_numeric(
        f_value_df["f_value"],
        errors="coerce",
    )

    f_value_df = f_value_df[
        f_value_df["f_value"].notna()
    ]

    if not f_value_df.empty:

        fig_f_value = px.histogram(
            f_value_df,
            x="f_value",
            nbins=12,

            labels={
                "f_value": "Risk F-Value",
            },
        )

        fig_f_value.update_layout(
            height=360,

            xaxis_title="F-Value",
            yaxis_title="Number of Events",

            bargap=0.08,

            margin=dict(
                l=20,
                r=20,
                t=20,
                b=20,
            ),

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(
            fig_f_value,
            use_container_width=True,
        )

    else:

        st.info(
            "No F-value data is available."
        )


# ============================================================
# SECTION 2 — ORBITAL / CONJUNCTION DATA
# ============================================================

st.markdown("---")

st.subheader("🛰️ Conjunction Characteristics")

data_col1, data_col2 = st.columns(2)


# ============================================================
# MISS DISTANCE DISTRIBUTION
# ============================================================

with data_col1:

    fig_distance = px.histogram(
        df_events,
        x="miss_distance_km",
        color="risk_level",

        nbins=15,

        labels={
            "miss_distance_km":
                "Miss Distance (km)",

            "risk_level":
                "Risk Level",
        },

        color_discrete_map={
            "HIGH": "#ff3b30",
            "MEDIUM": "#ffb000",
            "LOW": "#00d084",
            "UNKNOWN": "#808080",
        },
    )

    fig_distance.update_layout(
        height=350,

        xaxis_title="Miss Distance (km)",
        yaxis_title="Event Count",

        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(
        fig_distance,
        use_container_width=True,
    )


# ============================================================
# RELATIVE VELOCITY DISTRIBUTION
# ============================================================

with data_col2:

    fig_velocity = px.histogram(
        df_events,
        x="relative_velocity_km_s",
        color="risk_level",

        nbins=15,

        labels={
            "relative_velocity_km_s":
                "Relative Velocity (km/s)",

            "risk_level":
                "Risk Level",
        },

        color_discrete_map={
            "HIGH": "#ff3b30",
            "MEDIUM": "#ffb000",
            "LOW": "#00d084",
            "UNKNOWN": "#808080",
        },
    )

    fig_velocity.update_layout(
        height=350,

        xaxis_title="Relative Velocity (km/s)",
        yaxis_title="Event Count",

        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(
        fig_velocity,
        use_container_width=True,
    )


# ============================================================
# SECTION 3 — CONJUNCTION ACTIVITY
# ============================================================

st.markdown("---")

st.subheader("📈 Conjunction Activity")


activity_df = df_events.copy()

activity_df = activity_df[
    activity_df["tca"].notna()
]

if not activity_df.empty:

    activity_df["Time"] = (
        activity_df["tca"]
        .dt.floor("6h")
    )

    activity = (
        activity_df
        .groupby(
            ["Time", "risk_level"]
        )
        .size()
        .reset_index(
            name="Events"
        )
    )

    fig_activity = px.area(
        activity,
        x="Time",
        y="Events",
        color="risk_level",
        markers=True,

        labels={
            "Time": "Predicted TCA Window",
            "Events": "Conjunction Events",
            "risk_level": "Risk Level",
        },

        color_discrete_map={
            "HIGH": "#ff3b30",
            "MEDIUM": "#ffb000",
            "LOW": "#00d084",
            "UNKNOWN": "#808080",
        },
    )

    fig_activity.update_layout(
        height=380,

        xaxis_title="Predicted TCA Window",
        yaxis_title="Conjunction Events",

        hovermode="x unified",

        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(
        fig_activity,
        use_container_width=True,
    )

else:

    st.info(
        "No valid TCA timestamps are available."
    )


# ============================================================
# SECTION 4 — HIGH PRIORITY WATCHLIST
# ============================================================

st.markdown("---")

st.subheader("🚨 Conjunction Watchlist")

st.caption(
    "Events are ordered by the calculated risk "
    "assessment and then by miss distance."
)


watchlist = df_events.copy()


# Sort by risk priority first
risk_priority = {
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
    "UNKNOWN": 4,
}

watchlist["risk_priority"] = (
    watchlist["risk_level"]
    .map(risk_priority)
    .fillna(4)
)


watchlist = (
    watchlist
    .sort_values(
        [
            "risk_priority",
            "miss_distance_km",
        ],
        ascending=[
            True,
            True,
        ],
    )
    .head(10)
    .copy()
)


watchlist = watchlist[
    [
        "conjunction_id",
        "object_a",
        "object_b",
        "tca",
        "miss_distance_km",
        "relative_velocity_km_s",
        "risk_level",
        "confidence",
        "f_value",
    ]
]


watchlist.columns = [
    "Conjunction ID",
    "Object A",
    "Object B",
    "TCA (UTC)",
    "Miss Distance (km)",
    "Relative Velocity (km/s)",
    "Risk",
    "Confidence",
    "F-Value",
]


st.dataframe(
    watchlist,
    use_container_width=True,
    hide_index=True,

    column_config={

        "TCA (UTC)":
            st.column_config.DatetimeColumn(
                format="YYYY-MM-DD HH:mm:ss"
            ),

        "Miss Distance (km)":
            st.column_config.NumberColumn(
                format="%.2f km"
            ),

        "Relative Velocity (km/s)":
            st.column_config.NumberColumn(
                format="%.2f km/s"
            ),

        "F-Value":
            st.column_config.NumberColumn(
                format="%.3f"
            ),
    },
)


# ============================================================
# SECTION 5 — NEXT TCA
# ============================================================

st.markdown("---")

st.subheader(
    "⏱️ Next Critical Time of Closest Approach"
)


next_col1, next_col2, next_col3 = st.columns(3)


# ============================================================
# OBJECT PAIR
# ============================================================

with next_col1:

    st.markdown(
        "### 🛰️ Object Pair"
    )

    st.write(
        str(next_event["object_a"])
    )

    st.write("↓")

    st.write(
        str(next_event["object_b"])
    )


# ============================================================
# TCA
# ============================================================

with next_col2:

    st.markdown(
        "### 📅 TCA"
    )

    if pd.notna(next_event["tca"]):

        st.write(
            next_event["tca"].strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )
        )

        if hours_to_next_tca is not None:

            st.caption(
                f"{hours_to_next_tca:.1f} hours remaining"
            )

    else:

        st.write("Unavailable")


# ============================================================
# ASSESSMENT
# ============================================================

with next_col3:

    st.markdown(
        "### ⚠️ Assessment"
    )

    st.write(
        f"Risk: **{next_event['risk_level']}**"
    )

    st.write(
        "Miss Distance: "
        f"**{next_event['miss_distance_km']:.2f} km**"
    )

    if pd.notna(next_event["f_value"]):

        st.write(
            "F-Value: "
            f"**{next_event['f_value']:.3f}**"
        )

    st.write(
        "Confidence: "
        f"**{next_event['confidence']}**"
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "DebriX • Space Situational Awareness "
    "& Collision Risk Intelligence"
)