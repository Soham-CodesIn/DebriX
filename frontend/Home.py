from pathlib import Path

import pandas as pd
import streamlit as st  # type: ignore[import-not-found]

from api import (
    get_alerts,
    get_conjunctions,
    get_objects,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="DEBRIS-X",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent


# =========================================================
# LOAD GLOBAL CSS
# =========================================================

style_path = BASE_DIR / "style.css"

if style_path.exists():

    with open(
        style_path,
        "r",
        encoding="utf-8",
    ) as f:

        css = f.read()

    st.markdown(
        f"<style>{css}</style>",
        unsafe_allow_html=True,
    )


# =========================================================
# HOME PAGE CSS
# =========================================================

st.markdown(
    """
<style>

.stApp {
    background: transparent !important;
}

[data-testid="stAppViewContainer"] {
    background: transparent !important;
}

[data-testid="stHeader"] {
    background: rgba(0, 0, 0, 0.35) !important;
}


/* =====================================================
   BACKGROUND VIDEO
   ===================================================== */

#debrix-bg-video {
    position: fixed;
    top: 0;
    left: 0;

    width: 100vw;
    height: 100vh;

    object-fit: cover;

    z-index: -10;

    pointer-events: none;
}

#debrix-bg-overlay {
    position: fixed;
    top: 0;
    left: 0;

    width: 100vw;
    height: 100vh;

    background:
        linear-gradient(
            180deg,
            rgba(0, 0, 0, 0.28),
            rgba(0, 0, 0, 0.52) 55%,
            rgba(0, 0, 0, 0.78)
        );

    z-index: -9;

    pointer-events: none;
}


/* =====================================================
   CONTENT
   ===================================================== */

.block-container {
    max-width: 1450px !important;

    padding-top: 4rem !important;
    padding-bottom: 3rem !important;
}


/* =====================================================
   HERO
   ===================================================== */

.debrix-hero {
    text-align: center;

    padding-top: 5vh;
    padding-bottom: 4vh;

    color: white;

    text-shadow:
        0 3px 15px rgba(0, 0, 0, 0.95),
        0 0 30px rgba(0, 0, 0, 0.8);
}

.debrix-title {
    font-size: clamp(5rem, 11vw, 10rem);

    line-height: 0.9;

    font-weight: 900;

    letter-spacing: 0.08em;

    color: white;
}

.debrix-subtitle {
    margin-top: 3rem;

    font-size: clamp(1.2rem, 2vw, 2rem);

    font-weight: 500;

    color: #eafcff;

    letter-spacing: 0.03em;
}

.debrix-description {
    margin-top: 1.4rem;

    font-size: clamp(1rem, 1.4vw, 1.3rem);

    color: white;

    opacity: 0.95;
}


/* =====================================================
   METRIC CARDS
   ===================================================== */

.home-metric {
    text-align: center;

    min-height: 105px;

    padding: 18px 12px;

    border-radius: 14px;

    background:
        rgba(0, 0, 0, 0.48);

    border:
        1px solid
        rgba(255, 255, 255, 0.22);

    box-shadow:
        0 8px 30px
        rgba(0, 0, 0, 0.40);

    backdrop-filter: blur(7px);
}

.home-metric-label {
    font-size: 0.95rem;

    color: #e5e5e5;

    font-weight: 600;

    margin-bottom: 8px;
}

.home-metric-value {
    font-size: 2.1rem;

    color: white;

    font-weight: 800;
}


/* =====================================================
   NAVIGATION
   ===================================================== */

.navigation-heading {
    text-align: center;

    margin-top: 3.8rem;
    margin-bottom: 1.2rem;

    color: white;

    font-size: 0.95rem;

    letter-spacing: 0.2em;

    text-transform: uppercase;

    font-weight: 700;
}


/* =====================================================
   NAVIGATION BUTTONS
   ===================================================== */

div.stButton > button {
    width: 100% !important;

    min-height: 76px !important;

    border-radius: 14px !important;

    border:
        1px solid
        rgba(255, 255, 255, 0.45) !important;

    background:
        rgba(3, 10, 17, 0.92) !important;

    color: white !important;

    font-size: 1rem !important;

    font-weight: 800 !important;

    letter-spacing: 0.04em !important;

    box-shadow:
        0 8px 25px
        rgba(0, 0, 0, 0.55) !important;

    transition:
        all 0.18s ease !important;
}

div.stButton > button:hover {
    transform: translateY(-3px) !important;

    background:
        rgba(30, 50, 65, 0.96) !important;

    border-color:
        rgba(255, 255, 255, 0.85) !important;

    color: white !important;

    box-shadow:
        0 14px 35px
        rgba(0, 0, 0, 0.7) !important;
}

div.stButton > button p {
    color: white !important;

    font-weight: 800 !important;
}


/* =====================================================
   STATUS
   ===================================================== */

.backend-status {
    text-align: center;

    margin-top: 1.5rem;

    font-size: 0.85rem;
}

.backend-online {
    color: #b8f7d4;
}

.backend-offline {
    color: #ffb5b5;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# BACKGROUND VIDEO
# =========================================================

video_url = (
    "https://www.pexels.com/download/video/10296173/"
)

# Keep the video HTML as a single line so Streamlit's
# Markdown parser cannot interpret its child elements as
# Markdown code blocks.

st.markdown(
    f'<video id="debrix-bg-video" autoplay muted loop playsinline><source src="{video_url}" type="video/mp4"></video><div id="debrix-bg-overlay"></div>',
    unsafe_allow_html=True,
)


# =========================================================
# LOAD BACKEND DATA
# =========================================================

objects = []
conjunctions = []
alerts = []

backend_error = None

try:

    objects = get_objects()
    conjunctions = get_conjunctions()
    alerts = get_alerts()

except Exception as exc:

    backend_error = str(exc)


# =========================================================
# NORMALIZE API RESPONSES
# =========================================================

def normalize_list(data):

    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        possible_keys = [
            "objects",
            "conjunctions",
            "alerts",
            "data",
            "results",
            "items",
            "value",
        ]

        for key in possible_keys:

            value = data.get(key)

            if isinstance(value, list):
                return value

    return []


objects = normalize_list(objects)
conjunctions = normalize_list(conjunctions)
alerts = normalize_list(alerts)


# =========================================================
# CALCULATE METRICS
# =========================================================

tracked_objects = len(objects)


# ---------------------------------------------------------
# Upcoming conjunctions
# ---------------------------------------------------------

now_utc = pd.Timestamp.now(tz="UTC")

upcoming_count = 0

for conjunction in conjunctions:

    tca_value = conjunction.get("tca")

    if not tca_value:
        continue

    try:

        tca = pd.Timestamp(tca_value)

        if tca.tzinfo is None:

            tca = tca.tz_localize("UTC")

        else:

            tca = tca.tz_convert("UTC")

        if tca >= now_utc:

            upcoming_count += 1

    except Exception:

        continue


# ---------------------------------------------------------
# High-risk objects
# ---------------------------------------------------------

high_risk_objects = set()

for conjunction in conjunctions:

    risk = (
        conjunction.get(
            "risk_assessment"
        )
        or {}
    )

    risk_level = str(
        risk.get(
            "risk_level",
            ""
        )
    ).upper()

    if risk_level in {
        "HIGH",
        "CRITICAL",
    }:

        object_a = conjunction.get(
            "object_a"
        )

        object_b = conjunction.get(
            "object_b"
        )

        if object_a is not None:

            high_risk_objects.add(
                str(object_a)
            )

        if object_b is not None:

            high_risk_objects.add(
                str(object_b)
            )


high_risk_count = len(
    high_risk_objects
)


# ---------------------------------------------------------
# Debris count
# ---------------------------------------------------------

debris_count = 0

for obj in objects:

    object_type = str(
        obj.get(
            "object_type",
            ""
        )
    ).strip().lower()

    if (
        "debris" in object_type
        or "rocket body" in object_type
        or "rocket_body" in object_type
        or object_type in {
            "debris",
            "rocket",
            "fragment",
        }
    ):

        debris_count += 1


# =========================================================
# HERO
# =========================================================

st.markdown(
    '<div class="debrix-hero"><div class="debrix-title">DEBRIS-X</div><div class="debrix-subtitle">AI-based Debris Detection and Space Situational Awareness System</div><div class="debrix-description">We use public orbital tracking data to identify and prioritize potentially dangerous close approaches</div></div>',
    unsafe_allow_html=True,
)


# =========================================================
# METRICS
# =========================================================

metric_col1, metric_col2, metric_col3, metric_col4 = (
    st.columns(4)
)


with metric_col1:

    st.markdown(
        f'<div class="home-metric"><div class="home-metric-label">Tracked Objects</div><div class="home-metric-value">{tracked_objects:,}</div></div>',
        unsafe_allow_html=True,
    )


with metric_col2:

    st.markdown(
        f'<div class="home-metric"><div class="home-metric-label">Upcoming Conjunctions</div><div class="home-metric-value">{upcoming_count:,}</div></div>',
        unsafe_allow_html=True,
    )


with metric_col3:

    st.markdown(
        f'<div class="home-metric"><div class="home-metric-label">High-Risk Objects</div><div class="home-metric-value">{high_risk_count:,}</div></div>',
        unsafe_allow_html=True,
    )


with metric_col4:

    st.markdown(
        f'<div class="home-metric"><div class="home-metric-label">Debris Count</div><div class="home-metric-value">{debris_count:,}</div></div>',
        unsafe_allow_html=True,
    )


# =========================================================
# BACKEND STATUS
# =========================================================

if backend_error:

    st.markdown(
        '<div class="backend-status backend-offline">⚠ Backend unavailable — start the DebriX API to load live data.</div>',
        unsafe_allow_html=True,
    )

else:

    st.markdown(
        '<div class="backend-status backend-online">● Live orbital data connected</div>',
        unsafe_allow_html=True,
    )


# =========================================================
# NAVIGATION
# =========================================================

st.markdown(
    '<div class="navigation-heading">MISSION CONTROL</div>',
    unsafe_allow_html=True,
)


nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(
    4,
    gap="medium",
)


with nav_col1:

    if st.button(
        "📊  DASHBOARD",
        key="home_dashboard",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/01Dashboard.py"
        )


with nav_col2:

    if st.button(
        "🌍  3D ORBIT VIEW",
        key="home_3d",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/02View3D.py"
        )


with nav_col3:

    if st.button(
        "⚠️  COLLISION RISK",
        key="home_alerts",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/03Alerts.py"
        )


with nav_col4:

    if st.button(
        "🔎  EXPLORER",
        key="home_explorer",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/04Explorer.py"
        )