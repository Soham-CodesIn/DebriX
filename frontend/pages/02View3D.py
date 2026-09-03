import sys
from pathlib import Path
from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# IMPORT FRONTEND API
# ============================================================

sys.path.append(
    str(Path(__file__).resolve().parents[1])
)

from api import (
    get_conjunctions,
    get_objects,
    get_trajectory,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="DebriX — 3D Orbital View",
    page_icon="🛰️",
    layout="wide",
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def build_earth():

    import numpy as np

    phi = np.linspace(
        0,
        2 * np.pi,
        60
    )

    theta = np.linspace(
        -np.pi / 2,
        np.pi / 2,
        30
    )

    x = np.outer(
        np.cos(phi),
        np.cos(theta)
    )

    y = np.outer(
        np.sin(phi),
        np.cos(theta)
    )

    z = np.outer(
        np.ones_like(phi),
        np.sin(theta)
    )

    return go.Surface(
        x=x,
        y=y,
        z=z,
        opacity=0.65,
        showscale=False,
        name="Earth",
        hoverinfo="skip",
    )


def extract_points(trajectory):

    rows = []

    for point in trajectory.get(
        "points",
        []
    ):

        if point.get(
            "propagation_status"
        ) != "ok":

            continue

        position = point.get(
            "position_km",
            {}
        )

        if (
            position.get("x") is None
            or position.get("y") is None
            or position.get("z") is None
        ):

            continue

        rows.append(
            {
                "time": pd.to_datetime(
                    point["time_utc"],
                    utc=True,
                ),

                "x": position["x"],
                "y": position["y"],
                "z": position["z"],
            }
        )

    return pd.DataFrame(rows)


def distance_km(a, b):

    return (
        (a["x"] - b["x"]) ** 2
        + (a["y"] - b["y"]) ** 2
        + (a["z"] - b["z"]) ** 2
    ) ** 0.5


def closest_to_time(df, target):

    differences = abs(
        df["time"] - target
    )

    index = differences.idxmin()

    return df.loc[index]


def parse_tca(value):

    timestamp = pd.Timestamp(value)

    if timestamp.tzinfo is None:

        timestamp = timestamp.tz_localize(
            "UTC"
        )

    else:

        timestamp = timestamp.tz_convert(
            "UTC"
        )

    return timestamp


# ============================================================
# HEADER
# ============================================================

st.title(
    "🛰️ 3D Orbital Visualization"
)

st.caption(
    "Real orbital trajectories generated using TLE data and SGP4 propagation."
)


# ============================================================
# LOAD CONJUNCTIONS
# ============================================================

try:

    conjunctions = get_conjunctions()

except Exception as exc:

    st.error(
        "Unable to connect to the DebriX backend. "
        "Make sure Flask is running on "
        "http://127.0.0.1:5000."
    )

    st.code(str(exc))

    st.stop()


if not conjunctions:

    st.warning(
        "No conjunction data is currently available."
    )

    st.stop()


# ============================================================
# LOAD OBJECT NAMES
# ============================================================

try:

    objects = get_objects()

except Exception as exc:

    st.error(
        "Unable to load object information "
        "from the backend."
    )

    st.code(str(exc))

    st.stop()


object_names = {
    str(obj["object_id"]): (
        obj.get("name")
        or f"Object {obj['object_id']}"
    )
    for obj in objects
}


# ============================================================
# CONJUNCTION OPTIONS
# ============================================================

options = {}

for conjunction in conjunctions:

    conjunction_id = conjunction.get(
        "conjunction_id"
    )

    if not conjunction_id:
        continue

    object_a = str(
        conjunction.get(
            "object_a"
        )
    )

    object_b = str(
        conjunction.get(
            "object_b"
        )
    )

    object_a_name = object_names.get(
        object_a,
        f"Object {object_a}",
    )

    object_b_name = object_names.get(
        object_b,
        f"Object {object_b}",
    )

    miss_distance = conjunction.get(
        "miss_distance_km",
        float("nan"),
    )

    try:

        distance_text = (
            f"{float(miss_distance):.2f} km"
        )

    except Exception:

        distance_text = "N/A"


    label = (
        f"{conjunction_id}  |  "
        f"{object_a_name} ↔ "
        f"{object_b_name}  |  "
        f"{distance_text}"
    )

    options[label] = conjunction


if not options:

    st.warning(
        "No valid conjunction records are available."
    )

    st.stop()


# ============================================================
# READ CONJUNCTION FROM URL
#
# Explorer / Alerts will send:
#
# ?conjunction=131_82_20260903T135921
#
# ============================================================

requested_conjunction = (
    st.query_params.get(
        "conjunction"
    )
)


option_labels = list(
    options.keys()
)


selected_index = 0


if requested_conjunction:

    for index, label in enumerate(
        option_labels
    ):

        candidate = options[label].get(
            "conjunction_id"
        )

        if str(candidate) == str(
            requested_conjunction
        ):

            selected_index = index
            break


# ============================================================
# CONJUNCTION SELECTOR
# ============================================================

selected_label = st.selectbox(
    "Select a conjunction",
    option_labels,
    index=selected_index,
)


selected = options[
    selected_label
]


# ============================================================
# INTEGRATION STATUS
# ============================================================

selected_conjunction_id = str(
    selected.get(
        "conjunction_id"
    )
)


if requested_conjunction and (
    str(requested_conjunction)
    == selected_conjunction_id
):

    st.success(
        "Loaded conjunction from Explorer / Collision Risk."
    )


# Keep URL synchronized with the currently selected event.
st.query_params["conjunction"] = (
    selected_conjunction_id
)


# ============================================================
# SELECTED OBJECTS
# ============================================================

object_a = str(
    selected["object_a"]
)

object_b = str(
    selected["object_b"]
)


object_a_name = object_names.get(
    object_a,
    f"Object {object_a}",
)

object_b_name = object_names.get(
    object_b,
    f"Object {object_b}",
)


# ============================================================
# TCA
# ============================================================

tca = parse_tca(
    selected["tca"]
)


# ============================================================
# TRAJECTORY SETTINGS
# ============================================================

st.subheader(
    "Trajectory Window"
)

col1, col2, col3 = st.columns(3)


with col1:

    window_minutes = st.slider(
        "Minutes around TCA",
        min_value=10,
        max_value=180,
        value=60,
        step=10,
    )


with col2:

    trajectory_steps = st.slider(
        "Trajectory resolution",
        min_value=50,
        max_value=300,
        value=150,
        step=25,
    )


with col3:

    st.metric(
        "TCA",
        tca.strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        ),
    )


# ============================================================
# CALCULATE TIME WINDOW
# ============================================================

start = (
    tca
    - timedelta(
        minutes=window_minutes
    )
)

end = (
    tca
    + timedelta(
        minutes=window_minutes
    )
)


# ============================================================
# LOAD SGP4 TRAJECTORY
# ============================================================

@st.cache_data(ttl=30)
def load_trajectory(
    object_id,
    start_iso,
    end_iso,
    steps,
):

    return get_trajectory(
        object_id=object_id,
        start=start_iso,
        end=end_iso,
        steps=steps,
    )


try:

    trajectory_a = load_trajectory(
        object_a,
        start.isoformat(),
        end.isoformat(),
        trajectory_steps,
    )

    trajectory_b = load_trajectory(
        object_b,
        start.isoformat(),
        end.isoformat(),
        trajectory_steps,
    )

except Exception as exc:

    st.error(
        "Unable to generate the orbital trajectory."
    )

    st.code(str(exc))

    st.stop()


# ============================================================
# CONVERT TRAJECTORIES
# ============================================================

df_a = extract_points(
    trajectory_a
)

df_b = extract_points(
    trajectory_b
)


if df_a.empty:

    st.error(
        f"No valid SGP4 trajectory points were "
        f"generated for {object_a_name}."
    )

    st.stop()


if df_b.empty:

    st.error(
        f"No valid SGP4 trajectory points were "
        f"generated for {object_b_name}."
    )

    st.stop()


# ============================================================
# FIND TCA POSITIONS
# ============================================================

tca_a = closest_to_time(
    df_a,
    tca,
)

tca_b = closest_to_time(
    df_b,
    tca,
)


calculated_tca_distance = distance_km(
    tca_a,
    tca_b,
)


# ============================================================
# CONJUNCTION INFORMATION
# ============================================================

st.subheader(
    "Conjunction Information"
)

metric1, metric2, metric3, metric4 = (
    st.columns(4)
)


with metric1:

    st.metric(
        "Object A",
        object_a_name,
        help=f"Catalog ID: {object_a}",
    )


with metric2:

    st.metric(
        "Object B",
        object_b_name,
        help=f"Catalog ID: {object_b}",
    )


with metric3:

    try:

        catalog_distance = float(
            selected[
                "miss_distance_km"
            ]
        )

        distance_value = (
            f"{catalog_distance:.2f} km"
        )

    except Exception:

        distance_value = "N/A"


    st.metric(
        "Catalog Miss Distance",
        distance_value,
    )


with metric4:

    st.metric(
        "SGP4 TCA Separation",
        f"{calculated_tca_distance:.2f} km",
    )


# ============================================================
# TIME SLIDER
# ============================================================

st.subheader(
    "Time Control"
)


time_values = sorted(
    set(
        df_a["time"].tolist()
    )
    &
    set(
        df_b["time"].tolist()
    )
)


if not time_values:

    st.warning(
        "The two trajectories do not share "
        "common timestamps."
    )

    st.stop()


selected_time = st.select_slider(
    "Move through the conjunction timeline",
    options=time_values,
    value=min(
        time_values,
        key=lambda x: abs(x - tca),
    ),
    format_func=lambda value:
        value.strftime(
            "%H:%M:%S UTC"
        ),
)


# ============================================================
# CURRENT POSITIONS
# ============================================================

current_a = closest_to_time(
    df_a,
    selected_time,
)

current_b = closest_to_time(
    df_b,
    selected_time,
)


current_distance = distance_km(
    current_a,
    current_b,
)


# ============================================================
# 3D FIGURE
# ============================================================

fig = go.Figure()


# ------------------------------------------------------------
# Earth
# ------------------------------------------------------------

fig.add_trace(
    build_earth()
)


# ------------------------------------------------------------
# Object A Orbit
# ------------------------------------------------------------

fig.add_trace(
    go.Scatter3d(
        x=df_a["x"],
        y=df_a["y"],
        z=df_a["z"],
        mode="lines",
        name=f"{object_a_name} Orbit",
        line=dict(
            width=5,
        ),
        hovertemplate=(
            f"<b>{object_a_name}</b><br>"
            f"Catalog ID: {object_a}<br>"
            "X: %{x:.1f} km<br>"
            "Y: %{y:.1f} km<br>"
            "Z: %{z:.1f} km"
            "<extra></extra>"
        ),
    )
)


# ------------------------------------------------------------
# Object B Orbit
# ------------------------------------------------------------

fig.add_trace(
    go.Scatter3d(
        x=df_b["x"],
        y=df_b["y"],
        z=df_b["z"],
        mode="lines",
        name=f"{object_b_name} Orbit",
        line=dict(
            width=5,
        ),
        hovertemplate=(
            f"<b>{object_b_name}</b><br>"
            f"Catalog ID: {object_b}<br>"
            "X: %{x:.1f} km<br>"
            "Y: %{y:.1f} km<br>"
            "Z: %{z:.1f} km"
            "<extra></extra>"
        ),
    )
)


# ------------------------------------------------------------
# Current Object A
# ------------------------------------------------------------

fig.add_trace(
    go.Scatter3d(
        x=[current_a["x"]],
        y=[current_a["y"]],
        z=[current_a["z"]],
        mode="markers",
        name=f"{object_a_name} — Current",
        marker=dict(
            size=9,
        ),
        hovertemplate=(
            f"<b>{object_a_name}</b><br>"
            f"Catalog ID: {object_a}<br>"
            "Current position"
            "<extra></extra>"
        ),
    )
)


# ------------------------------------------------------------
# Current Object B
# ------------------------------------------------------------

fig.add_trace(
    go.Scatter3d(
        x=[current_b["x"]],
        y=[current_b["y"]],
        z=[current_b["z"]],
        mode="markers",
        name=f"{object_b_name} — Current",
        marker=dict(
            size=9,
        ),
        hovertemplate=(
            f"<b>{object_b_name}</b><br>"
            f"Catalog ID: {object_b}<br>"
            "Current position"
            "<extra></extra>"
        ),
    )
)


# ------------------------------------------------------------
# TCA Object A
# ------------------------------------------------------------

fig.add_trace(
    go.Scatter3d(
        x=[tca_a["x"]],
        y=[tca_a["y"]],
        z=[tca_a["z"]],
        mode="markers",
        name=f"{object_a_name} — TCA",
        marker=dict(
            size=7,
            symbol="diamond",
        ),
        hovertemplate=(
            f"<b>{object_a_name}</b><br>"
            f"Catalog ID: {object_a}<br>"
            "Position at TCA"
            "<extra></extra>"
        ),
    )
)


# ------------------------------------------------------------
# TCA Object B
# ------------------------------------------------------------

fig.add_trace(
    go.Scatter3d(
        x=[tca_b["x"]],
        y=[tca_b["y"]],
        z=[tca_b["z"]],
        mode="markers",
        name=f"{object_b_name} — TCA",
        marker=dict(
            size=7,
            symbol="diamond",
        ),
        hovertemplate=(
            f"<b>{object_b_name}</b><br>"
            f"Catalog ID: {object_b}<br>"
            "Position at TCA"
            "<extra></extra>"
        ),
    )
)


# ------------------------------------------------------------
# Current Separation Vector
# ------------------------------------------------------------

fig.add_trace(
    go.Scatter3d(
        x=[
            current_a["x"],
            current_b["x"],
        ],

        y=[
            current_a["y"],
            current_b["y"],
        ],

        z=[
            current_a["z"],
            current_b["z"],
        ],

        mode="lines",

        name="Current Separation",

        line=dict(
            width=7,
            dash="dash",
        ),

        hovertemplate=(
            "Current separation"
            "<extra></extra>"
        ),
    )
)


# ============================================================
# FIGURE LAYOUT
# ============================================================

fig.update_layout(
    height=720,

    margin=dict(
        l=0,
        r=0,
        t=30,
        b=0,
    ),

    scene=dict(
        xaxis_title="TEME X (km)",
        yaxis_title="TEME Y (km)",
        zaxis_title="TEME Z (km)",
        aspectmode="data",
    ),

    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=0.01,
        xanchor="left",
        x=0.01,
    ),
)


# ============================================================
# DISPLAY 3D VISUALIZATION
# ============================================================

st.plotly_chart(
    fig,
    use_container_width=True,
)


# ============================================================
# SELECTED TIME INFORMATION
# ============================================================

st.subheader(
    "Selected Time"
)

state1, state2, state3 = (
    st.columns(3)
)


with state1:

    st.metric(
        "Selected Time",
        selected_time.strftime(
            "%H:%M:%S UTC"
        ),
    )


with state2:

    st.metric(
        "Object Separation",
        f"{current_distance:.2f} km",
    )


with state3:

    offset_minutes = (
        selected_time - tca
    ).total_seconds() / 60

    st.metric(
        "Offset from TCA",
        f"{offset_minutes:+.1f} min",
    )


# ============================================================
# TCA DETAILS
# ============================================================

with st.expander(
    "TCA Details"
):

    st.write(
        {
            "conjunction_id":
                selected[
                    "conjunction_id"
                ],

            "object_a": {
                "name": object_a_name,
                "catalog_id": object_a,
            },

            "object_b": {
                "name": object_b_name,
                "catalog_id": object_b,
            },

            "tca":
                selected["tca"],

            "catalog_miss_distance_km":
                selected[
                    "miss_distance_km"
                ],

            "sgp4_tca_separation_km":
                calculated_tca_distance,

            "relative_velocity_km_s":
                selected.get(
                    "relative_velocity_km_s"
                ),

            "object_a_trajectory_points":
                len(df_a),

            "object_b_trajectory_points":
                len(df_b),

            "frame":
                trajectory_a.get(
                    "frame"
                ),
        }
    )