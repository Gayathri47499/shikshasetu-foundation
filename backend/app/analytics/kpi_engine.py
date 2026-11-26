from datetime import date, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.models.entities import (
    AttendanceRecord,
    Intervention,
    InterventionOutcome,
    OutreachWorker,
    RiskAssessment,
    School,
    Student,
    VisitSchedule,
)

settings = get_settings()


def compute_dashboard_summary(
    db: Session,
    school_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    allowed_school_id: Optional[int] = None,
) -> Dict:
    """Calculate all Foundation Dashboard metrics directly from backend database state."""
    effective_school_id = allowed_school_id if allowed_school_id is not None else school_id

    schools_q = db.query(School).order_by(School.id)
    if effective_school_id is not None:
        schools_q = schools_q.filter(School.id == effective_school_id)
    schools = schools_q.all()

    total_schools = len(schools)
    total_enrolled = sum(s.enrolled_students for s in schools)
    weighted_att = (
        round(sum(s.enrolled_students * s.baseline_attendance_pct for s in schools) / total_enrolled, 2)
        if total_enrolled > 0
        else 0.0
    )

    # Students & current risk assessments
    students_q = db.query(Student)
    if effective_school_id is not None:
        students_q = students_q.filter(Student.school_id == effective_school_id)
    students = students_q.all()
    student_ids = [s.id for s in students]

    assessments = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.is_current.is_(True))
        .all()
    )
    if effective_school_id is not None:
        assessments = [a for a in assessments if a.student_id in set(student_ids)]

    priority_counts = {"High Priority": 0, "Review Soon": 0, "Routine Review": 0}
    for a in assessments:
        priority_counts[a.effective_band] = priority_counts.get(a.effective_band, 0) + 1

    students_requiring_review = priority_counts["High Priority"] + priority_counts["Review Soon"]
    high_priority_cases = priority_counts["High Priority"]

    # Interventions & weekly capacity/budget
    int_q = db.query(Intervention).options(joinedload(Intervention.outcomes))
    if effective_school_id is not None:
        int_q = int_q.filter(Intervention.school_id == effective_school_id)
    if date_from is not None:
        int_q = int_q.filter(Intervention.scheduled_date >= date_from)
    if date_to is not None:
        int_q = int_q.filter(Intervention.scheduled_date <= date_to)
    interventions = int_q.all()

    status_breakdown = {"proposed": 0, "pending": 0, "completed": 0, "cancelled": 0, "rescheduled": 0}
    for iv in interventions:
        status_breakdown[iv.status] = status_breakdown.get(iv.status, 0) + 1

    active_weekly_visits = sum(
        1
        for iv in interventions
        if iv.approval_status == "approved" and iv.status in ("pending", "completed", "rescheduled")
    )
    remaining_visit_capacity = max(0, settings.MAX_WEEKLY_VISITS - active_weekly_visits)
    weekly_budget_used = sum(
        iv.estimated_cost_inr
        for iv in interventions
        if iv.approval_status == "approved" and iv.status in ("pending", "completed", "rescheduled")
    )

    pending_followups = 0
    for iv in interventions:
        if iv.status == "completed":
            has_pending_followup = any(
                o.follow_up_required and not o.follow_up_completed for o in iv.outcomes
            )
            if has_pending_followup or len(iv.outcomes) == 0:
                pending_followups += 1
        elif iv.status in ("pending", "rescheduled"):
            pending_followups += 1

    # School-wise attendance comparison
    school_comparison = [
        {
            "school_id": s.id,
            "code": s.code,
            "name": s.name,
            "enrolled_students": s.enrolled_students,
            "attendance_pct": s.baseline_attendance_pct,
            "requires_attention": s.baseline_attendance_pct < 70.0,
        }
        for s in schools
    ]

    # Weekly & monthly attendance trends from attendance_records
    att_q = db.query(AttendanceRecord)
    if effective_school_id is not None:
        att_q = att_q.filter(AttendanceRecord.school_id == effective_school_id)
    att_records = att_q.order_by(AttendanceRecord.record_date.asc()).all()

    weekly_buckets: Dict[str, List[float]] = {}
    weekly_sources: Dict[str, str] = {}
    for r in att_records:
        weekly_buckets.setdefault(r.week_label, []).append(r.attendance_pct)
        weekly_sources[r.week_label] = r.data_source

    weekly_trends = [
        {
            "week": wk,
            "avg_attendance_pct": round(sum(vals) / len(vals), 2),
            "sample_size": len(vals),
            "data_source": weekly_sources.get(wk, "unknown"),
        }
        for wk, vals in weekly_buckets.items()
    ]

    # Outreach worker workload performance
    workers = db.query(OutreachWorker).order_by(OutreachWorker.id).all()
    outreach_performance = []
    for w in workers:
        w_ints = [iv for iv in interventions if iv.worker_id == w.id]
        outreach_performance.append(
            {
                "worker_id": w.id,
                "name": w.name,
                "assigned_visits": len(w_ints),
                "completed": sum(1 for iv in w_ints if iv.status == "completed"),
                "pending": sum(1 for iv in w_ints if iv.status in ("pending", "rescheduled")),
                "weekly_capacity": w.max_daily_visits * w.working_days_per_week,
            }
        )

    return {
        "kpis": {
            "total_students_enrolled": total_enrolled,
            "tracked_student_profiles": len(students),
            "total_schools": total_schools,
            "average_attendance_pct": weighted_att,
            "students_requiring_review": students_requiring_review,
            "high_priority_cases": high_priority_cases,
            "weekly_intervention_visits": active_weekly_visits,
            "max_weekly_visits": settings.MAX_WEEKLY_VISITS,
            "remaining_visit_capacity": remaining_visit_capacity,
            "weekly_budget_used_inr": weekly_budget_used,
            "weekly_budget_limit_inr": settings.WEEKLY_BUDGET_INR,
            "budget_utilization_pct": round((weekly_budget_used / settings.WEEKLY_BUDGET_INR) * 100, 1)
            if settings.WEEKLY_BUDGET_INR > 0
            else 0.0,
            "completed_interventions": status_breakdown["completed"],
            "pending_followups": pending_followups,
        },
        "charts": {
            "school_attendance": school_comparison,
            "weekly_trends": weekly_trends,
            "priority_distribution": [
                {"band": k, "count": v} for k, v in priority_counts.items()
            ],
            "intervention_status": [
                {"status": k.title(), "count": v} for k, v in status_breakdown.items()
            ],
            "outreach_performance": outreach_performance,
        },
        "data_freshness": {
            "assessment_baseline": "Veltris Challenge A Dataset A1/A2/A3 (Exact Values)",
            "synthetic_disclaimer": (
                "The 12 student profiles and multi-week trend series are synthetic/illustrative assessment data. "
                "Simulated trends are clearly tagged and never presented as real dropout outcomes."
            ),
        },
    }


def compute_impact_kpis(
    db: Session,
    school_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> Dict:
    """
    Compute the 8 social-impact KPIs required by Task F & Section 4.J.
    Carefully distinguishes verified/recorded metrics from illustrative baseline data
    and includes non-causation methodology notes.
    """
    schools_q = db.query(School)
    if school_id is not None:
        schools_q = schools_q.filter(School.id == school_id)
    schools = schools_q.all()

    total_enrolled = sum(s.enrolled_students for s in schools)
    avg_attendance = (
        round(sum(s.enrolled_students * s.baseline_attendance_pct for s in schools) / total_enrolled, 2)
        if total_enrolled > 0
        else 0.0
    )

    students_q = db.query(Student)
    if school_id is not None:
        students_q = students_q.filter(Student.school_id == school_id)
    students = students_q.all()

    # Prolonged absenteeism defined transparently as attendance < 50%
    prolonged_threshold = 50.0
    prolonged_count = sum(1 for s in students if s.attendance_pct < prolonged_threshold)
    prolonged_share = round((prolonged_count / len(students)) * 100, 1) if students else 0.0

    int_q = db.query(Intervention).options(joinedload(Intervention.outcomes))
    if school_id is not None:
        int_q = int_q.filter(Intervention.school_id == school_id)
    if date_from is not None:
        int_q = int_q.filter(Intervention.scheduled_date >= date_from)
    if date_to is not None:
        int_q = int_q.filter(Intervention.scheduled_date <= date_to)
    interventions = int_q.all()

    scheduled_count = sum(1 for iv in interventions if iv.approval_status == "approved" and iv.status != "cancelled")
    completed_list = [iv for iv in interventions if iv.status == "completed"]
    completed_count = len(completed_list)
    completion_rate = round((completed_count / scheduled_count) * 100, 1) if scheduled_count > 0 else 0.0

    # Follow-ups due & completed
    all_outcomes = [o for iv in interventions for o in iv.outcomes]
    followups_due = sum(1 for o in all_outcomes if o.follow_up_required)
    followups_done = sum(1 for o in all_outcomes if o.follow_up_required and o.follow_up_completed)
    followup_rate = round((followups_done / followups_due) * 100, 1) if followups_due > 0 else 0.0

    # Retention under defined cohort rule: enrolled status / total tracked students
    retained_count = sum(1 for s in students if s.enrollment_status == "enrolled")
    retention_rate = round((retained_count / len(students)) * 100, 1) if students else 0.0

    # Attendance change before vs after intervention (only where both measurements exist)
    deltas: List[float] = []
    improved_students = 0
    needs_additional_review = 0
    before_after_series = []
    for iv in completed_list:
        if iv.pre_attendance_pct is not None and iv.post_attendance_pct is not None:
            delta = round(iv.post_attendance_pct - iv.pre_attendance_pct, 2)
            deltas.append(delta)
            if delta > 0:
                improved_students += 1
            else:
                needs_additional_review += 1
            before_after_series.append(
                {
                    "student_id": iv.student_id,
                    "intervention_id": iv.id,
                    "pre_attendance_pct": iv.pre_attendance_pct,
                    "post_attendance_pct": iv.post_attendance_pct,
                    "change_pct": delta,
                }
            )

    avg_att_change = round(sum(deltas) / len(deltas), 2) if deltas else None

    # Outreach cost per successful support outcome
    # Successful support outcome = completed visit with agreed support plan OR post-visit improvement > 0
    successful_outcomes = sum(
        1
        for iv in completed_list
        if any(
            o.visit_completed and o.outcome_category in ("Contacted - Support Plan Agreed", "Attendance Stabilizing")
            for o in iv.outcomes
        )
    )
    total_spend = sum(iv.estimated_cost_inr for iv in completed_list)
    cost_per_success = round(total_spend / successful_outcomes, 2) if successful_outcomes > 0 else None

    # Time to first review (hours from assessment creation to teacher review)
    assessments = db.query(RiskAssessment).filter(RiskAssessment.is_current.is_(True)).all()
    if school_id is not None:
        sid_set = {s.id for s in students}
        assessments = [a for a in assessments if a.student_id in sid_set]
    review_hours = [
        round((a.reviewed_at - a.created_at).total_seconds() / 3600.0, 1)
        for a in assessments
        if a.reviewed_at is not None and a.created_at is not None
    ]
    avg_time_to_review_hrs = round(sum(review_hours) / len(review_hours), 1) if review_hours else None

    return {
        "kpis": [
            {
                "id": "avg_attendance",
                "name": "Average Attendance",
                "value": f"{avg_attendance:.2f}%",
                "numeric_value": avg_attendance,
                "definition": "Weighted average attendance across selected schools (enrolled-weighted).",
                "data_label": "Veltris Dataset A1 Baseline",
            },
            {
                "id": "prolonged_absenteeism",
                "name": "Prolonged Absenteeism (<50%)",
                "value": f"{prolonged_count} / {len(students)} ({prolonged_share}%)",
                "numeric_value": prolonged_share,
                "definition": "Share of tracked student profiles below the 50% attendance threshold.",
                "data_label": "Veltris Dataset A2 (Synthetic Prototype)",
            },
            {
                "id": "intervention_completion",
                "name": "Intervention Completion Rate",
                "value": f"{completion_rate}%",
                "numeric_value": completion_rate,
                "definition": "Completed visits divided by approved non-cancelled scheduled visits.",
                "data_label": "Platform Workflow Records",
            },
            {
                "id": "followup_completion",
                "name": "Follow-up Completion Rate",
                "value": f"{followup_rate}%",
                "numeric_value": followup_rate,
                "definition": "Completed follow-ups divided by total follow-ups marked due.",
                "data_label": "Platform Outcome Records",
            },
            {
                "id": "student_retention",
                "name": "Cohort Student Retention",
                "value": f"{retention_rate}%",
                "numeric_value": retention_rate,
                "definition": "Students continuing active enrollment under defined cohort status.",
                "data_label": "Tracked Student Profiles",
            },
            {
                "id": "cost_per_success",
                "name": "Outreach Cost / Successful Outcome",
                "value": f"INR {cost_per_success:,.0f}" if cost_per_success is not None else "Insufficient outcome data",
                "numeric_value": cost_per_success,
                "definition": "Total completed outreach spend (INR 250/visit) divided by visits with an agreed support plan or stabilizing attendance.",
                "data_label": "Platform Operational Metric",
            },
            {
                "id": "time_to_first_review",
                "name": "Median/Avg Time to First Review",
                "value": f"{avg_time_to_review_hrs} hrs" if avg_time_to_review_hrs is not None else "Awaiting reviews",
                "numeric_value": avg_time_to_review_hrs,
                "definition": "Elapsed hours from automated risk-flag generation to teacher review.",
                "data_label": "Audit Timestamp Metric",
            },
            {
                "id": "attendance_change",
                "name": "Post-Intervention Attendance Change",
                "value": (
                    f"{'+' if avg_att_change >= 0 else ''}{avg_att_change}%"
                    if avg_att_change is not None
                    else "Awaiting post-visit logs"
                ),
                "numeric_value": avg_att_change,
                "definition": "Post-intervention attendance minus comparable pre-intervention attendance.",
                "data_label": "Descriptive Association Only",
            },
        ],
        "outcome_analytics": {
            "total_interventions": len(interventions),
            "completed": completed_count,
            "pending": sum(1 for iv in interventions if iv.status in ("pending", "rescheduled")),
            "proposed": sum(1 for iv in interventions if iv.status == "proposed"),
            "cancelled": sum(1 for iv in interventions if iv.status == "cancelled"),
            "followups_due": followups_due - followups_done,
            "improved_attendance_count": improved_students,
            "requires_additional_review_count": needs_additional_review,
            "before_after_series": before_after_series,
        },
        "ninety_day_plan": [
            {
                "phase": "Days 1-30: Baseline & Pilot",
                "activities": "Verify school CSV data quality, calibrate threshold assumptions with teachers, deploy monitoring queue.",
                "evidence": "Baseline KPI snapshot, import validation logs, reviewed queue.",
            },
            {
                "phase": "Days 31-60: Supported Rollout",
                "activities": "Operate teacher-approved weekly outreach plans within 100-visit / INR 25,000 caps; record visit outcomes.",
                "evidence": "Visit completion rates, override reasons, follow-up logs.",
            },
            {
                "phase": "Days 61-90: Impact Evaluation",
                "activities": "Compare post-intervention attendance against baseline and comparison groups; inspect subgroup fairness.",
                "evidence": "90-day KPI report, limitations review, governance sign-off.",
            },
        ],
        "causal_disclaimer": (
            "Descriptive before/after attendance comparisons track monitoring progress only and do NOT prove "
            "that an intervention caused the attendance change. External factors (holidays, illness, weather, "
            "exams, family context) must be evaluated with educators and a comparison cohort."
        ),
    }
