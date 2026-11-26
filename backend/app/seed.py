from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.intelligence.risk_engine import evaluate_student_priority
from app.models.entities import (
    AcademicRecord,
    AttendanceRecord,
    AuditEvent,
    Intervention,
    InterventionOutcome,
    Notification,
    OutreachWorker,
    RiskAssessment,
    Role,
    School,
    Student,
    User,
)

# Exact Dataset A1 from Veltris Vertical AI Academy Challenge A
DATASET_A1_SCHOOLS = [
    {"id": 1, "code": "SCH01", "name": "School 1", "enrolled_students": 100, "baseline_attendance_pct": 82.0, "coordinator": "Meera Nair"},
    {"id": 2, "code": "SCH02", "name": "School 2", "enrolled_students": 95, "baseline_attendance_pct": 76.0, "coordinator": "Rohan Verma"},
    {"id": 3, "code": "SCH03", "name": "School 3", "enrolled_students": 90, "baseline_attendance_pct": 72.0, "coordinator": "Anita Sharma"},
    {"id": 4, "code": "SCH04", "name": "School 4", "enrolled_students": 85, "baseline_attendance_pct": 68.0, "coordinator": "Suresh Patel"},
    {"id": 5, "code": "SCH05", "name": "School 5", "enrolled_students": 100, "baseline_attendance_pct": 65.0, "coordinator": "Kavita Joshi"},
    {"id": 6, "code": "SCH06", "name": "School 6", "enrolled_students": 80, "baseline_attendance_pct": 80.0, "coordinator": "Deepak Kulkarni"},
    {"id": 7, "code": "SCH07", "name": "School 7", "enrolled_students": 90, "baseline_attendance_pct": 61.0, "coordinator": "Priya Deshmukh"},
    {"id": 8, "code": "SCH08", "name": "School 8", "enrolled_students": 85, "baseline_attendance_pct": 74.0, "coordinator": "Vikram Singh"},
    {"id": 9, "code": "SCH09", "name": "School 9", "enrolled_students": 90, "baseline_attendance_pct": 70.0, "coordinator": "Sunita Rao"},
    {"id": 10, "code": "SCH10", "name": "School 10", "enrolled_students": 85, "baseline_attendance_pct": 62.0, "coordinator": "Manoj Tiwari"},
]

# Exact Dataset A2 from Veltris Vertical AI Academy Challenge A (12 synthetic student records)
DATASET_A2_STUDENTS = [
    {"id": "ST001", "school_id": 1, "attendance_pct": 92.0, "previous_term_score": 78.0, "distance_km": 1.0, "prior_intervention_count": 0},
    {"id": "ST002", "school_id": 1, "attendance_pct": 54.0, "previous_term_score": 62.0, "distance_km": 4.0, "prior_intervention_count": 1},
    {"id": "ST003", "school_id": 2, "attendance_pct": 68.0, "previous_term_score": 71.0, "distance_km": 3.0, "prior_intervention_count": 0},
    {"id": "ST004", "school_id": 3, "attendance_pct": 41.0, "previous_term_score": 45.0, "distance_km": 6.0, "prior_intervention_count": 2},
    {"id": "ST005", "school_id": 3, "attendance_pct": 83.0, "previous_term_score": 81.0, "distance_km": 2.0, "prior_intervention_count": 0},
    {"id": "ST006", "school_id": 4, "attendance_pct": 59.0, "previous_term_score": 52.0, "distance_km": 5.0, "prior_intervention_count": 1},
    {"id": "ST007", "school_id": 5, "attendance_pct": 48.0, "previous_term_score": 58.0, "distance_km": 7.0, "prior_intervention_count": 0},
    {"id": "ST008", "school_id": 6, "attendance_pct": 88.0, "previous_term_score": 85.0, "distance_km": 1.0, "prior_intervention_count": 0},
    {"id": "ST009", "school_id": 7, "attendance_pct": 35.0, "previous_term_score": 39.0, "distance_km": 8.0, "prior_intervention_count": 2},
    {"id": "ST010", "school_id": 8, "attendance_pct": 72.0, "previous_term_score": 68.0, "distance_km": 3.0, "prior_intervention_count": 0},
    {"id": "ST011", "school_id": 9, "attendance_pct": 57.0, "previous_term_score": 60.0, "distance_km": 4.0, "prior_intervention_count": 1},
    {"id": "ST012", "school_id": 10, "attendance_pct": 44.0, "previous_term_score": 48.0, "distance_km": 6.0, "prior_intervention_count": 0},
]

# Exact Dataset A3: 5 Outreach Workers, max 4 visits/worker/day, 5 days/week
DATASET_A3_WORKERS = [
    {"id": "OW01", "name": "Aarav Kulkarni", "cluster_schools": [1, 2], "max_daily_visits": 4, "working_days_per_week": 5},
    {"id": "OW02", "name": "Bhavna Meena", "cluster_schools": [3, 4], "max_daily_visits": 4, "working_days_per_week": 5},
    {"id": "OW03", "name": "Chetan Gowda", "cluster_schools": [5, 6], "max_daily_visits": 4, "working_days_per_week": 5},
    {"id": "OW04", "name": "Divya Nair", "cluster_schools": [7, 8], "max_daily_visits": 4, "working_days_per_week": 5},
    {"id": "OW05", "name": "Eshan Yadav", "cluster_schools": [9, 10], "max_daily_visits": 4, "working_days_per_week": 5},
]


def seed_database(db: Session) -> None:
    """Idempotently populate exact Veltris Challenge A datasets and initial workflow records."""
    if db.query(School).count() > 0:
        return

    # 1. Roles
    roles_data = [
        ("admin", "Foundation Administrator", "Full administrative access across all 10 schools, imports, budget, and reports."),
        ("teacher", "Teacher Coordinator", "School-scoped student review, risk override validation, and visit approval."),
        ("outreach", "Community Outreach Worker", "Assigned visit schedule execution, outcome logging, and offline field drafts."),
    ]
    role_map = {}
    for name, display, desc in roles_data:
        r = Role(name=name, display_name=display, description=desc)
        db.add(r)
        db.flush()
        role_map[name] = r

    # 2. Schools (Dataset A1)
    for sc in DATASET_A1_SCHOOLS:
        db.add(
            School(
                id=sc["id"],
                code=sc["code"],
                name=sc["name"],
                district="Semi-Urban & Rural Cluster",
                enrolled_students=sc["enrolled_students"],
                baseline_attendance_pct=sc["baseline_attendance_pct"],
                coordinator_name=sc["coordinator"],
                status="active",
                data_source="veltris_assessment_a1",
            )
        )
    db.flush()

    # 3. Default Users for all 3 roles
    demo_users = [
        {
            "email": "admin@shikshasetu.org",
            "full_name": "Ananya Iyer (Foundation Director)",
            "password": "Admin@123",
            "role": "admin",
            "school_id": None,
            "worker_id": None,
        },
        {
            "email": "teacher.school7@shikshasetu.org",
            "full_name": "Priya Deshmukh (School 7 Coordinator)",
            "password": "Teacher@123",
            "role": "teacher",
            "school_id": 7,
            "worker_id": None,
        },
        {
            "email": "teacher.school3@shikshasetu.org",
            "full_name": "Anita Sharma (School 3 Coordinator)",
            "password": "Teacher@123",
            "role": "teacher",
            "school_id": 3,
            "worker_id": None,
        },
        {
            "email": "outreach.ow04@shikshasetu.org",
            "full_name": "Divya Nair (Outreach Worker OW04)",
            "password": "Outreach@123",
            "role": "outreach",
            "school_id": None,
            "worker_id": "OW04",
        },
    ]
    admin_user = None
    for u in demo_users:
        user_obj = User(
            email=u["email"],
            full_name=u["full_name"],
            password_hash=hash_password(u["password"]),
            role_id=role_map[u["role"]].id,
            assigned_school_id=u["school_id"],
            assigned_worker_id=u["worker_id"],
            is_active=True,
        )
        db.add(user_obj)
        db.flush()
        if u["role"] == "admin":
            admin_user = user_obj

    # 4. Outreach Workers (Dataset A3)
    for w in DATASET_A3_WORKERS:
        db.add(OutreachWorker(**w, is_active=True))
    db.flush()

    # 5. Students (Dataset A2) + Baseline Academic & Attendance records + Prior Interventions
    today = date.today()
    # Anchor Monday of current week
    week_monday = today - timedelta(days=today.weekday())

    for st_data in DATASET_A2_STUDENTS:
        st = Student(
            id=st_data["id"],
            school_id=st_data["school_id"],
            grade_level="Grade 7",
            enrollment_status="enrolled",
            attendance_pct=st_data["attendance_pct"],
            previous_term_score=st_data["previous_term_score"],
            distance_km=st_data["distance_km"],
            prior_intervention_count=st_data["prior_intervention_count"],
            teacher_observations=(
                "High-priority attendance & travel barrier check requested."
                if st_data["attendance_pct"] < 50
                else "Monitoring under weekly school attendance register."
            ),
            is_synthetic_assessment=True,
            data_source="veltris_assessment_a2",
        )
        db.add(st)

        # Academic record
        db.add(
            AcademicRecord(
                student_id=st.id,
                term="Previous Term",
                assessment_type="Term Assessment",
                score=st_data["previous_term_score"],
                data_source="veltris_assessment_a2",
            )
        )

        # Current baseline attendance record (Dataset A2 exact value) + 3 prior illustrative weekly points
        # Clearly tagged so users know multi-week series are synthetic baselines anchored at Dataset A2
        weekly_offsets = [
            ("2026-W44", today - timedelta(days=21), min(100.0, st_data["attendance_pct"] + 4.0), "illustrative_weekly_trend"),
            ("2026-W45", today - timedelta(days=14), min(100.0, st_data["attendance_pct"] + 2.0), "illustrative_weekly_trend"),
            ("2026-W46", today - timedelta(days=7), st_data["attendance_pct"], "veltris_assessment_a2"),
        ]
        for wk_label, r_date, att_val, src in weekly_offsets:
            db.add(
                AttendanceRecord(
                    student_id=st.id,
                    school_id=st.school_id,
                    week_label=wk_label,
                    record_date=r_date,
                    attendance_pct=att_val,
                    days_present=round((att_val / 100.0) * 5),
                    days_scheduled=5,
                    consecutive_absences=3 if att_val < 45 else (2 if att_val < 60 else 0),
                    data_source=src,
                )
            )

    db.flush()

    # 6. Seed prior visits matching Dataset A2 exactly (ST002: 1, ST004: 2, ST006: 1, ST009: 2, ST011: 1)
    # Marked as prior historical visits awaiting documented outcome review (matching case study:
    # "intervention outcomes are not consistently recorded")
    worker_for_school = {s_id: w["id"] for w in DATASET_A3_WORKERS for s_id in w["cluster_schools"]}
    for st_data in DATASET_A2_STUDENTS:
        cnt = st_data["prior_intervention_count"]
        for i in range(cnt):
            iv = Intervention(
                student_id=st_data["id"],
                school_id=st_data["school_id"],
                worker_id=worker_for_school.get(st_data["school_id"], "OW01"),
                intervention_type="Household Visit",
                scheduled_date=week_monday - timedelta(days=7 * (i + 1)),
                status="completed",
                approval_status="approved",
                approved_by_id=admin_user.id if admin_user else None,
                estimated_cost_inr=250.0,
                pre_attendance_pct=st_data["attendance_pct"],
                post_attendance_pct=None,
                teacher_notes="Historical assessment record: prior household visit logged without standardized outcome.",
                data_source="veltris_assessment_a2",
            )
            db.add(iv)

    # Add 1 active approved upcoming visit for OW04 (ST009 follow-up review) so Outreach Worker view has live data
    # while keeping ST009's pending outcome review clear
    db.flush()

    # 7. Compute initial transparent Risk Assessments for all 12 students
    for st_data in DATASET_A2_STUDENTS:
        pending_review_cnt = st_data["prior_intervention_count"]
        eval_res = evaluate_student_priority(
            student_id=st_data["id"],
            attendance_pct=st_data["attendance_pct"],
            previous_term_score=st_data["previous_term_score"],
            distance_km=st_data["distance_km"],
            prior_intervention_count=st_data["prior_intervention_count"],
            pending_outcome_review_count=pending_review_cnt,
        )
        db.add(
            RiskAssessment(
                student_id=st_data["id"],
                version=eval_res["version"],
                priority_score=eval_res["priority_score"],
                computed_band=eval_res["computed_band"],
                effective_band=eval_res["effective_band"],
                component_scores=eval_res["component_scores"],
                contributing_factors=eval_res["contributing_factors"],
                reason_codes=eval_res["reason_codes"],
                missing_data_flags=eval_res["missing_data_flags"],
                recommended_next_step=eval_res["recommended_next_step"],
                validation_status="pending_review",
                is_current=True,
            )
        )

    # 8. Initial Notifications
    notifications = [
        Notification(
            target_role="admin",
            category="review_recommendation",
            severity="urgent",
            title="Initial Investigation Shortlist Ready (5 Priority Cases)",
            message="ST009 (35%), ST004 (41%), ST012 (44%), ST007 (48%), and ST002 (54%) are flagged for coordinator verification.",
            reference_type="risk_queue",
            reference_id="ST009",
        ),
        Notification(
            target_role="teacher",
            category="pending_validation",
            severity="warning",
            title="School 7 Attendance Below Baseline (61%)",
            message="School 7 currently has the lowest average attendance (61%). Please review ST009 indicators and prior visit outcomes.",
            reference_type="school",
            reference_id="7",
        ),
        Notification(
            target_role="outreach",
            category="overdue_followup",
            severity="warning",
            title="7 Historical Visits Missing Outcome Documentation",
            message="Prior household visits for ST002, ST004, ST006, ST009, and ST011 require standardized outcome recording.",
            reference_type="interventions",
            reference_id="pending",
        ),
        Notification(
            target_role=None,
            category="weekly_summary",
            severity="info",
            title="Weekly Capacity & Budget Ready",
            message="5 outreach workers active: 100 max weekly visits and INR 25,000 weekly operational budget configured.",
            reference_type="planner",
            reference_id="weekly",
        ),
    ]
    db.add_all(notifications)

    # 9. Initial Audit Event
    db.add(
        AuditEvent(
            actor_id=admin_user.id if admin_user else None,
            actor_email="system@shikshasetu.org",
            actor_role="system",
            action="seed_veltris_datasets",
            record_type="foundation",
            record_id="A1-A2-A3",
            reason="Populated exact Veltris Challenge A datasets (10 schools/900 students, 12 synthetic students, 5 workers/INR 25,000 budget).",
        )
    )
    db.commit()
