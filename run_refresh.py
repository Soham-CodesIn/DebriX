import os
from dotenv import load_dotenv
from backend.data.database import SessionLocal, init_db
from backend.jobs.refresh_catalog import run_refresh_catalog
from backend.data.repository import get_all_conjunctions, get_risk_assessment, get_object

load_dotenv()

init_db()
session = SessionLocal()

result = run_refresh_catalog(
    session,
    os.environ["SPACETRACK_USER"],
    os.environ["SPACETRACK_PASS"],
    ingest_limit=50,
)
print(result)

print()
print(f"{'Conjunction ID':<35} {'Object A':<25} {'Object B':<25} {'Miss (km)':>10} {'RelVel':>8} {'F-Value':>8} {'Risk':<10}")
for c in get_all_conjunctions(session):
    risk = get_risk_assessment(session, c.conjunction_id)
    obj_a = get_object(session, c.object_a)
    obj_b = get_object(session, c.object_b)
    name_a = obj_a.name if obj_a and obj_a.name else c.object_a
    name_b = obj_b.name if obj_b and obj_b.name else c.object_b
    risk_level = risk.risk_level if risk else "none"
    f_value = f"{risk.f_value:.3f}" if risk else "n/a"
    print(f"{c.conjunction_id:<35} {name_a:<25} {name_b:<25} {c.miss_distance_km:>10.3f} {c.relative_velocity_km_s:>8.2f} {f_value:>8} {risk_level:<10}")

session.close()