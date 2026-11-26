import csv
import io
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.security import get_current_user, log_audit_event, require_roles
from app.config import get_settings
from app.database import get_db
from app.intelligence.planner_engine import generate_proposed_weekly_plan, validate_weekly_constraints
from app.models.entities import Intervention, OutreachWorker, RiskAssessment, Student, User, VisitSchedule
from app.schemas.api import PlannerApprovalRequest, PlannerProposeRequest

router = APIRouter(prefix="/api/planner", tags=["Intelligent Intervention Planner"])
settings = get_settings()


def _default_week_monday() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


@router.get("/weekly")
def get_weekly_plan(
    week_start_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    monday = week_start_date or _default_week_monday()
    workers = db.query(OutreachWorker).order_by(OutreachWorker.id).all()
    q = db.query(VisitSchedule).filter(VisitSchedule.week_start_date == monday)
    if current_user.role_obj.name == "outreach" and current_user.assigned_worker_id:
        q = q.filter(VisitSchedule.worker_id == current_user.assigned_worker_id)
        q = q.filter(VisitSchedule.approval_status == "approved")
    elif current_user.role_obj.name == "teacher" and current_user.assigned_school_id is not None:
        q = q.filter(VisitSchedule.school_id == current_user.assigned_school_id)

    schedules = q.order_by(VisitSchedule.visit_date.asc(), VisitSchedule.priority_score_snapshot.desc()).all()
    worker_map = {w.id: w.name for w in workers}

    all_week_schedules = db.query(VisitSchedule).filter(VisitSchedule.week_start_date == monday).all()
    approved_active = [
        {
            "worker_id": s.worker_id,
            "visit_date": s.visit_date,
            "estimated_cost_inr": s.estimated_cost_inr,
        }
        for s in all_week_schedules
        if s.approval_status == "approved" and s.visit_status != "cancelled"
    ]
    _, violations, constraint_summary = validate_weekly_constraints(
        proposed_visits=[],
        workers=[{"id": w.id, "max_daily_visits": w.max_daily_visits} for w in workers],
        existing_approved_visits=approved_active,
    )

    worker_workload = []
    for w in workers:
        w_approved = [s for s in all_week_schedules if s.worker_id == w.id and s.approval_status == "approved" and s.visit_status != "cancelled"]
        w_proposed = [s for s in all_week_schedules if s.worker_id == w.id and s.approval_status == "proposed"]
        worker_workload.append(
            {
                "worker_id": w.id,
                "name": w.name,
                "cluster_schools": w.cluster_schools,
                "approved_visits": len(w_approved),
                "proposed_visits": len(w_proposed),
                "weekly_capacity": w.max_daily_visits * w.working_days_per_week,
                "max_daily_visits": w.max_daily_visits,
            }
        )

    return {
        "week_start_date": monday.isoformat(),
        "schedules": [
            {
                "id": s.id,
                "visit_date": s.visit_date.isoformat(),
                "worker_id": s.worker_id,
                "worker_name": worker_map.get(s.worker_id, s.worker_id),
                "student_id": s.student_id,
                "school_id": s.school_id,
                "intervention_id": s.intervention_id,
                "priority_score_snapshot": s.priority_score_snapshot,
                "priority_band_snapshot": s.priority_band_snapshot,
                "approval_status": s.approval_status,
                "visit_status": s.visit_status,
                "estimated_cost_inr": s.estimated_cost_inr,
                "rationale": s.rationale,
            }
            for s in schedules
        ],
        "constraints": constraint_summary,
        "constraint_violations": violations,
        "worker_workload": worker_workload,
    }


@router.post("/propose")
def propose_weekly_plan(
    payload: PlannerProposeRequest,
    current_user: User = Depends(require_roles("admin", "teacher")),
    db: Session = Depends(get_db),
):
    workers = [
        {
            "id": w.id,
            "name": w.name,
            "cluster_schools": w.cluster_schools,
            "max_daily_visits": w.max_daily_visits,
            "is_active": w.is_active,
        }
        for w in db.query(OutreachWorker).all()
    ]
    students_q = db.query(Student)
    if current_user.role_obj.name == "teacher" and current_user.assigned_school_id is not None:
        students_q = students_q.filter(Student.school_id == current_user.assigned_school_id)
    students = students_q.all()

    assessments = {
        a.student_id: a
        for a in db.query(RiskAssessment).filter(RiskAssessment.is_current.is_(True)).all()
    }
    candidates = [
        {
            "student_id": s.id,
            "school_id": s.school_id,
            "priority_score": assessments[s.id].priority_score if s.id in assessments else 0.0,
            "effective_band": assessments[s.id].effective_band if s.id in assessments else "Routine Review",
        }
        for s in students
    ]

    existing = [
        {
            "student_id": v.student_id,
            "worker_id": v.worker_id,
            "visit_date": v.visit_date,
            "visit_status": v.visit_status,
            "approval_status": v.approval_status,
            "estimated_cost_inr": v.estimated_cost_inr,
        }
        for v in db.query(VisitSchedule).filter(VisitSchedule.week_start_date == payload.week_start_date).all()
    ]

    plan = generate_proposed_weekly_plan(
        week_start_date=payload.week_start_date,
        candidate_students=candidates,
        workers=workers,
        existing_visits_in_week=existing,
        max_visits_to_propose=payload.max_visits_to_propose,
    )

    created_ids = []
    for prop in plan["proposals"]:
        vs = VisitSchedule(
            week_start_date=payload.week_start_date,
            visit_date=prop["visit_date"],
            worker_id=prop["worker_id"],
            student_id=prop["student_id"],
            school_id=prop["school_id"],
            priority_score_snapshot=prop["priority_score_snapshot"],
            priority_band_snapshot=prop["priority_band_snapshot"],
            approval_status="proposed",
            visit_status="pending",
            estimated_cost_inr=prop["estimated_cost_inr"],
            rationale=prop["rationale"],
        )
        db.add(vs)
        db.flush()
        created_ids.append(vs.id)

    log_audit_event(
        db,
        actor=current_user,
        action="planner_proposals_generated",
        record_type="visit_schedule",
        record_id=payload.week_start_date.isoformat(),
        details={"proposed_count": len(created_ids)},
    )
    db.commit()
    return {
        "message": f"Generated {len(created_ids)} proposed visit(s) awaiting Teacher/Admin approval.",
        "proposed_count": len(created_ids),
        "skipped": plan["skipped"],
    }


@router.post("/{schedule_id}/approve")
def approve_or_reject_schedule(
    schedule_id: int,
    payload: PlannerApprovalRequest,
    current_user: User = Depends(require_roles("admin", "teacher")),
    db: Session = Depends(get_db),
):
    vs = db.query(VisitSchedule).filter(VisitSchedule.id == schedule_id).first()
    if not vs:
        raise HTTPException(status_code=404, detail="Schedule entry not found.")
    if current_user.role_obj.name == "teacher" and current_user.assigned_school_id not in (None, vs.school_id):
        raise HTTPException(status_code=403, detail="Cannot approve visits outside your assigned school.")

    if payload.decision == "approved":
        workers = [{"id": w.id, "max_daily_visits": w.max_daily_visits} for w in db.query(OutreachWorker).all()]
        existing_approved = [
            {
                "worker_id": s.worker_id,
                "visit_date": s.visit_date,
                "estimated_cost_inr": s.estimated_cost_inr,
            }
            for s in db.query(VisitSchedule)
            .filter(
                VisitSchedule.week_start_date == vs.week_start_date,
                VisitSchedule.approval_status == "approved",
                VisitSchedule.visit_status != "cancelled",
                VisitSchedule.id != vs.id,
            )
            .all()
        ]
        ok, violations, _ = validate_weekly_constraints(
            proposed_visits=[
                {
                    "worker_id": vs.worker_id,
                    "visit_date": vs.visit_date,
                    "estimated_cost_inr": vs.estimated_cost_inr,
                }
            ],
            workers=workers,
            existing_approved_visits=existing_approved,
        )
        if not ok:
            raise HTTPException(status_code=400, detail="Constraint violation: " + " | ".join(violations))

        vs.approval_status = "approved"
        vs.approved_by_id = current_user.id

        # Create corresponding approved Intervention record if not yet linked
        if vs.intervention_id is None:
            st = db.query(Student).filter(Student.id == vs.student_id).first()
            iv = Intervention(
                student_id=vs.student_id,
                school_id=vs.school_id,
                worker_id=vs.worker_id,
                intervention_type="Household Visit",
                scheduled_date=vs.visit_date,
                status="pending",
                approval_status="approved",
                approved_by_id=current_user.id,
                estimated_cost_inr=vs.estimated_cost_inr,
                pre_attendance_pct=st.attendance_pct if st else None,
                teacher_notes=payload.notes or vs.rationale,
                data_source="planner_approved",
            )
            db.add(iv)
            db.flush()
            vs.intervention_id = iv.id
    else:
        vs.approval_status = "rejected"
        vs.visit_status = "cancelled"

    log_audit_event(
        db,
        actor=current_user,
        action=f"schedule_{payload.decision}",
        record_type="visit_schedule",
        record_id=str(vs.id),
        reason=payload.notes,
    )
    db.commit()
    return {"message": f"Schedule #{vs.id} {payload.decision}.", "intervention_id": vs.intervention_id}


@router.get("/offline-tasks/csv")
def download_offline_task_list(
    week_start_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Offline-friendly downloadable CSV task list for field outreach teams."""
    monday = week_start_date or _default_week_monday()
    q = db.query(VisitSchedule).filter(
        VisitSchedule.week_start_date == monday,
        VisitSchedule.approval_status == "approved",
    )
    if current_user.role_obj.name == "outreach" and current_user.assigned_worker_id:
        q = q.filter(VisitSchedule.worker_id == current_user.assigned_worker_id)
    rows = q.order_by(VisitSchedule.visit_date.asc()).all()

    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(
        ["schedule_id", "intervention_id", "visit_date", "worker_id", "student_id", "school_id", "priority_band", "visit_status"]
    )
    for r in rows:
        writer.writerow(
            [
                r.id,
                r.intervention_id or "",
                r.visit_date.isoformat(),
                r.worker_id,
                r.student_id,
                r.school_id,
                r.priority_band_snapshot,
                r.visit_status,
            ]
        )
    out.seek(0)
    return StreamingResponse(
        iter([out.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=shikshasetu_tasks_{monday.isoformat()}.csv"},
    )
