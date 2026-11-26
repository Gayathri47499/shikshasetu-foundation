from datetime import date, timedelta
import os
import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_shikshasetu.db"
os.environ["GEMINI_API_KEY"] = ""

from app.database import Base, SessionLocal, engine
from app.intelligence.planner_engine import generate_proposed_weekly_plan, validate_weekly_constraints
from app.intelligence.risk_engine import evaluate_student_priority
from app.main import app
from app.seed import seed_database


@pytest.fixture(scope="module")
def client():
    if os.path.exists("./test_shikshasetu.db"):
        os.remove("./test_shikshasetu.db")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    db.close()
    with TestClient(app) as c:
        yield c
    engine.dispose()
    if os.path.exists("./test_shikshasetu.db"):
        os.remove("./test_shikshasetu.db")


def _auth_header(client: TestClient, email: str, password: str) -> dict:
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_seed_exact_veltris_datasets(client: TestClient):
    headers = _auth_header(client, "admin@shikshasetu.org", "Admin@123")
    dash = client.get("/api/dashboard", headers=headers).json()
    assert dash["kpis"]["total_schools"] == 10
    assert dash["kpis"]["total_students_enrolled"] == 900
    assert dash["kpis"]["tracked_student_profiles"] == 12
    assert dash["kpis"]["max_weekly_visits"] == 100
    assert dash["kpis"]["weekly_budget_limit_inr"] == 25000.0


def test_risk_engine_transparency_and_safeguards():
    # Prior visit with documented outcome should NOT add followup penalty
    with_documented = evaluate_student_priority(
        student_id="ST_TEST",
        attendance_pct=70.0,
        previous_term_score=70.0,
        distance_km=2.0,
        prior_intervention_count=2,
        pending_outcome_review_count=0,
    )
    without_prior = evaluate_student_priority(
        student_id="ST_TEST_2",
        attendance_pct=70.0,
        previous_term_score=70.0,
        distance_km=2.0,
        prior_intervention_count=0,
        pending_outcome_review_count=0,
    )
    assert with_documented["priority_score"] == without_prior["priority_score"]

    # ST009 from Dataset A2 should rank High Priority
    st009 = evaluate_student_priority("ST009", 35.0, 39.0, 8.0, 2, 2)
    assert st009["computed_band"] == "High Priority"
    assert st009["priority_score"] >= 65.0
    assert "ATT_CRITICALLY_LOW" in st009["reason_codes"]


def test_planner_enforces_daily_weekly_and_budget_limits():
    monday = date(2026, 11, 30)
    workers = [
        {"id": f"OW0{i}", "name": f"Worker {i}", "cluster_schools": [i * 2 - 1, i * 2], "max_daily_visits": 4, "is_active": True}
        for i in range(1, 6)
    ]
    # 5 visits for same worker on same day must fail validation
    bad_visits = [
        {"worker_id": "OW01", "visit_date": monday, "estimated_cost_inr": 250.0}
        for _ in range(5)
    ]
    ok, violations, _ = validate_weekly_constraints(bad_visits, workers, [])
    assert not ok
    assert any("max 4/day" in v for v in violations)

    # 101 visits must fail weekly cap and budget cap
    too_many = [
        {"worker_id": f"OW0{(i % 5) + 1}", "visit_date": monday + timedelta(days=(i // 20) % 5), "estimated_cost_inr": 250.0}
        for i in range(101)
    ]
    ok2, violations2, _ = validate_weekly_constraints(too_many, workers, [])
    assert not ok2
    assert any("100" in v for v in violations2)
    assert any("25,000" in v for v in violations2)

    # Proposal generator respects caps and requires approval
    candidates = [
        {"student_id": f"S{i}", "school_id": (i % 10) + 1, "priority_score": 80 - i, "effective_band": "High Priority"}
        for i in range(12)
    ]
    plan = generate_proposed_weekly_plan(monday, candidates, workers, [], max_visits_to_propose=10)
    assert len(plan["proposals"]) == 10
    assert plan["approval_required"] is True
    assert all(p["approval_status"] == "proposed" for p in plan["proposals"])


def test_rbac_school_scoping_and_teacher_override(client: TestClient):
    teacher_headers = _auth_header(client, "teacher.school7@shikshasetu.org", "Teacher@123")
    # Teacher of School 7 cannot view School 1
    r_forbidden = client.get("/api/schools/1", headers=teacher_headers)
    assert r_forbidden.status_code == 403

    # Teacher of School 7 CAN view and override ST009 (School 7)
    r_override = client.post(
        "/api/risk/ST009/review",
        headers=teacher_headers,
        json={
            "validation_status": "validated",
            "override_reason": "Verified attendance register and transport distance barrier with family.",
        },
    )
    assert r_override.status_code == 200
    assert r_override.json()["validation_status"] == "validated"


def test_csv_validation_flags_invalid_rows(client: TestClient):
    admin_headers = _auth_header(client, "admin@shikshasetu.org", "Admin@123")
    outreach_headers = _auth_header(client, "outreach.ow04@shikshasetu.org", "Outreach@123")

    csv_content = (
        "id,school_id,attendance_pct,previous_term_score,distance_km\n"
        "ST099,7,55,60,3\n"
        "ST100,99,120,60,3\n"
    ).encode("utf-8")

    # Outreach worker cannot upload CSVs
    r_denied = client.post(
        "/api/imports/students/preview",
        headers=outreach_headers,
        files={"file": ("test.csv", csv_content, "text/csv")},
    )
    assert r_denied.status_code == 403

    # Admin preview catches invalid attendance 120% & unknown school 99
    r_prev = client.post(
        "/api/imports/students/preview",
        headers=admin_headers,
        files={"file": ("test.csv", csv_content, "text/csv")},
    )
    assert r_prev.status_code == 200
    data = r_prev.json()
    assert data["valid_count"] == 1
    assert data["error_count"] >= 2


def test_ai_assistant_and_reports(client: TestClient):
    admin_headers = _auth_header(client, "admin@shikshasetu.org", "Admin@123")
    r_ai = client.post(
        "/api/assistant/ask",
        headers=admin_headers,
        json={"question": "Why was ST009 prioritized?", "session_id": "test-sess"},
    )
    assert r_ai.status_code == 200
    body = r_ai.json()
    assert "ST009" in body["reply"]
    assert body["human_review_required"] is True

    r_pdf = client.get("/api/reports/impact/pdf", headers=admin_headers)
    assert r_pdf.status_code == 200
    assert r_pdf.content.startswith(b"%PDF")
