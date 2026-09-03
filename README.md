# DebriX

## AI-Based Space Situational Awareness and Collision Risk Detection Platform

DebriX is a Space Situational Awareness (SSA) platform designed to process publicly available orbital tracking data, detect potential conjunctions between satellites and space debris, assess collision risk, and visualize orbital information through an interactive web interface.

The project was developed for Smart India Hackathon 2026, Problem Statement SIH-2026-17-005, under the Space Technology theme.

## Key Features

- Orbital object tracking
- TLE data processing
- SGP4 orbital propagation
- Conjunction detection
- Deterministic collision risk assessment
- Time of Closest Approach (TCA) analysis
- 3D orbital visualization
- Collision alerts
- Conjunction Explorer
- Live dashboard
- Search, filtering, and sorting
- Explainable risk information
- Orbital propagation state inspection
- Data refresh pipeline
- End-to-end frontend and backend integration

## System Architecture

```text
             Public Orbital Data
                    |
                    v
             +--------------+
             |  TLE Dataset |
             +------+-------+
                    |
                    v
          +---------------------+
          | Data Ingestion and  |
          | Validation Pipeline |
          +----------+----------+
                     |
                     v
              +-------------+
              |   SQLite    |
              |   Database  |
              +------+------+
                     |
          +----------+----------+
          |                     |
          v                     v
 +-----------------+   +------------------+
 | SGP4 Propagation|   | Conjunction      |
 | Engine          |   | Screening        |
 +--------+--------+   +--------+---------+
          |                     |
          |                     v
          |             +-----------------+
          |             | Risk Assessment |
          |             +--------+--------+
          |                      |
          +----------+-----------+
                     |
                     v
              +-------------+
              | Flask REST  |
              | API         |
              +------+------+
                     |
                     v
             +---------------+
             |   Streamlit   |
             |   Frontend    |
             +-------+-------+
                     |
        +------------+------------+
        |            |             |
        v            v             v
    Dashboard      3D View       Alerts
                     |
                     v
                 Explorer
```

## Project Structure

```text
debrix/
|
├── backend/
│   ├── api/
│   │   ├── alerts.py
│   │   ├── conjunction.py
│   │   ├── health.py
│   │   ├── objects.py
│   │   └── propagation.py
│   │
│   ├── data/
│   │   ├── models.py
│   │   └── repository.py
│   │
│   ├── orbital/
│   │   └── propagation.py
│   │
│   └── app.py
│
├── frontend/
│   ├── pages/
│   │   ├── 01Dashboard.py
│   │   ├── 02View3D.py
│   │   ├── 03Alerts.py
│   │   └── 04Explorer.py
│   │
│   ├── api.py
│   ├── home.py
│   ├── style.css
│   └── requirements.txt
│
├── tests/
│
├── debrix.db
├── .env
├── requirements.txt
└── run_refresh.py
```

## Technology Stack

### Backend

- Python
- Flask
- SQLAlchemy
- SQLite
- SGP4

### Frontend

- Streamlit
- Pandas
- Plotly

### Orbital Analysis

- Two-Line Element (TLE) data
- SGP4 propagation
- TEME coordinate output
- Conjunction screening
- Time of Closest Approach
- Deterministic risk assessment

## Orbital Propagation

DebriX uses the SGP4 propagation model to calculate the position and velocity of an orbital object from its TLE data.

The propagation engine can generate orbital states for requested timestamps and is used by both:

1. 3D trajectory visualization
2. Conjunction analysis

The resulting trajectory data is presented in the TEME reference frame.

## Conjunction and Risk Analysis

A conjunction represents a potentially close approach between two tracked orbital objects.

For each detected conjunction, DebriX records information such as:

| Parameter | Description |
|---|---|
| Object A | First tracked object |
| Object B | Second tracked object |
| TCA | Time of Closest Approach |
| Miss Distance | Minimum separation between objects |
| Relative Velocity | Relative velocity at the conjunction |
| F-value | Deterministic risk feature |
| Risk Level | LOW, MEDIUM, HIGH, or CRITICAL |
| Confidence | Confidence associated with the assessment |
| Pc | Probability of collision, when available |

The platform does not fabricate Probability of Collision values when covariance information is unavailable.

Instead, the interface explicitly reports that Pc is unavailable and provides the reason.

## 3D Visualization

The 3D View provides an interactive visualization of:

- Earth
- Object A trajectory
- Object B trajectory
- Current object positions
- TCA positions
- Separation between objects
- Time relative to TCA

Users can select a conjunction and adjust:

- TCA-centered time window
- Trajectory resolution
- Position along the trajectory

The Explorer can also directly open a selected conjunction in the 3D viewer.

## Dashboard

The Dashboard provides a high-level overview of the current orbital environment.

It displays:

- Number of tracked objects
- Number of conjunction events
- High-risk events
- Medium-risk events
- Upcoming TCA
- Risk distribution
- Average F-value
- Conjunction information

All displayed values are obtained from the backend rather than being hard-coded mock values.

## Alerts

The Alerts page provides two types of events.

### Active Alerts

Generated by the backend when a conjunction reaches an elevated risk level.

### Monitoring Events

Real conjunctions that currently do not qualify as elevated-risk alerts.

This allows potentially relevant conjunctions to remain visible without incorrectly presenting every conjunction as a collision warning.

## Conjunction Explorer

The Explorer provides detailed access to detected conjunctions.

Users can:

- Search by object name
- Search by object ID
- Search by conjunction ID
- Filter by risk level
- Filter by confidence
- Filter by maximum miss distance
- Sort by upcoming TCA
- Sort by miss distance
- Sort by risk
- Sort by relative velocity
- Sort by F-value
- Inspect individual conjunctions
- View object information
- Inspect risk assessment
- Load orbital propagation state

### TCA Sorting

The Next TCA, soonest first option prioritizes future conjunctions according to how soon their TCA occurs.

Past conjunctions are placed afterward.

## Refreshing Orbital Data

The orbital dataset can be refreshed using:

```powershell
python run_refresh.py
```

The refresh pipeline updates the database and runs the relevant conjunction and risk analysis processes.

After refreshing the backend data, reload the Streamlit application to see the updated results.

## Running the Project

### 1. Activate the virtual environment

From the project root:

```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Start the Flask backend

```powershell
flask --app backend.app run --host 127.0.0.1 --port 5000
```

The backend will be available locally at:

```text
http://127.0.0.1:5000
```

### 3. Start the Streamlit frontend

In a second terminal:

```powershell
streamlit run frontend/home.py
```

The DebriX interface will then open in the browser.

## API Endpoints

| Endpoint | Purpose |
|---|---|
| `/health` | Backend health check |
| `/objects` | Retrieve tracked orbital objects |
| `/objects/<object_id>` | Retrieve a specific object |
| `/objects/<object_id>/propagation` | Retrieve orbital propagation state |
| `/objects/<object_id>/trajectory` | Generate orbital trajectory |
| `/conjunctions` | Retrieve detected conjunctions |
| `/conjunctions/<conjunction_id>` | Retrieve conjunction details |
| `/alerts` | Retrieve generated alerts |

## Data Flow

A typical DebriX analysis follows this process:

```text
TLE Data
   |
   v
Validation
   |
   v
Database Storage
   |
   v
SGP4 Propagation
   |
   v
Orbital Position Calculation
   |
   v
Conjunction Screening
   |
   v
TCA and Miss Distance
   |
   v
Risk Assessment
   |
   v
Alerts
   |
   v
Dashboard / 3D / Explorer
```

## Current Limitations

### Covariance and Probability of Collision

The current publicly available TLE-based pipeline does not provide the covariance information required for a statistically rigorous Probability of Collision calculation.

Therefore, Pc is reported as unavailable when covariance data is missing.

DebriX instead uses deterministic conjunction features for the current risk assessment.

### TLE Accuracy

TLE-based propagation is suitable for the project's prototype and demonstration purposes, but prediction accuracy decreases as the propagation time moves further from the TLE epoch.

### Public Data Dependency

The quality and freshness of the results depend on the availability and quality of the underlying orbital tracking data.

## Project Objective

The goal of DebriX is to provide an accessible software-based approach to Space Situational Awareness by combining orbital tracking data, propagation, conjunction analysis, collision risk assessment, and visualization into a single platform.

The system requires no dedicated tracking hardware and instead works with publicly available orbital data.

## Contribution

The project was developed collaboratively.

Arkaprabha provided the initial frontend structure and UI files.

The frontend was subsequently expanded and integrated with the backend, including:

- Real orbital data integration
- Backend API integration
- Risk assessment
- Collision alerts
- TCA analysis
- 3D orbital visualization
- Object information
- Propagation state inspection
- Search and filtering
- Sorting and upcoming-TCA prioritization
- Dynamic dashboard metrics
- Debugging and system integration

## Hackathon

Smart India Hackathon 2026

Problem Statement: SIH-2026-17-005

Theme: Space Technology

Project: DebriX, AI-Based Debris Detection and Space Situational Awareness Platform

## Project Status

Functional End-to-End Prototype

The current implementation supports the complete pipeline from orbital tracking data to propagation, conjunction detection, risk assessment, alerts, and interactive visualization.
