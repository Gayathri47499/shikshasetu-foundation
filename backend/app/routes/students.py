import csv
import io
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.auth.security import get_current_user, log_audit_event, require_roles
from app.database import get_db
from app.models.entities import (
    AcademicRecord,
    AttendanceRecord,
    Intervention,
    RiskAssessment,
    Student,
    User,
)
from app.schemas.api import ObservationUpdateRequest

router = APIRouter(prefix="/api/students", tags=["Student Management"])


def _get_authorized_students(db: Session, user: User):
    q = db.query(Student).options(joinedload(Student.school))
    role = user.role_obj.name
    if role == "teacher" and user.assigned_school_id is not None:
        q = q.filter(Student.school_id == user.assigned_school_id)
    elif role == "outreach" and user.assigned_worker_id:
        assigned_ids = [
            iv.student_id
            for iv in db.query(Intervention)
            .filter(Intervention.worker_id == user.assigned_worker_id)
            .all()
        ]
        q = q.filter(Student.id.in_(assigned_ids or ["__none__"]))
    return q


@router.get("")
def list_students(
    search: Optional[str] = Query(None),
    school_id: Optional[int] = Query(None),
    min_attendance: Optional[float] = Query(None, ge=0, le=100),
    max_attendance: Optional[float] = Query(None, ge=0, le=100),
    priority_band: Optional[str] = Query(None),
    intervention_status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = _get_authorized_students(db, current_user)
    if school_id is not None:
        q = q.filter(Student.school_id == school_id)
    if min_attendance is not None:
        q = q.filter(Student.attendance_pct >= min_attendance)
    if max_attendance is not None:
        q = q.filter(Student.attendance_pct <= max_attendance)
    if search:
        term = f"%{search.strip()}%"
        q = q.filter(Student.id.ilike(term))

    all_students = q.order_by(Student.id.asc()).all()
    assessments = {
        a.student_id: a
        for a in db.query(RiskAssessment).filter(RiskAssessment.is_current.is_(True)).all()
    }
    interventions = db.query(Intervention).all()
    int_by_student = {}
    for iv in interventions:
        int_by_student.setdefault(iv.student_id, []).append(iv)

    filtered = []
    for st in all_students:
        ra = assessments.get(st.id)
        band = ra.effective_band if ra else "Routine Review"
        if priority_band and band != priority_band:
            continue

        st_ints = int_by_student.get(st.id, [])
        latest_status = st_ints[-1].status if st_ints else "none"
        if intervention_status:
            if intervention_status == "none" and st_ints:
                continue
            elif intervention_status != "none" and not any(iv.status == intervention_status for iv in st_ints):
                continue

        filtered.append(
            {
                "id": st.id,
                "school_id": st.school_id,
                "school_name": st.school.name if st.school else f"School {st.school_id}",
                "grade_level": st.grade_level,
                "enrollment_status": st.enrollment_status,
                "attendance_pct": st.attendance_pct,
                "previous_term_score": st.previous_term_score,
                "distance_km": st.distance_km,
                "prior_intervention_count": st.prior_intervention_count,
                "priority_score": ra.priority_score if ra else 0.0,
                "priority_band": band,
                "validation_status": ra.validation_status if ra else "pending_review",
                "latest_intervention_status": latest_status,
                "is_synthetic_assessment": st.is_synthetic_assessment,
                "data_source": st.data_source,
            }
        )

    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": filtered[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


@router.get("/export/csv")
def export_students_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    students = _get_authorized_students(db, current_user).order_by(Student.id.asc()).all()
    assessments = {
        a.student_id: a
        for a in db.query(RiskAssessment).filter(RiskAssessment.is_current.is_(True)).all()
    }

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "student_id",
            "school_id",
            "attendance_pct",
            "previous_term_score",
            "distance_km",
            "prior_intervention_count",
            "priority_score",
            "priority_band",
            "validation_status",
            "data_source",
        ]
    )
    for s in students:
        ra = assessments.get(s.id)
        writer.writerow(
            [
                s.id,
                s.school_id,
                s.attendance_pct,
                s.previous_term_score,
                s.distance_km,
                s.prior_intervention_count,
                ra.priority_score if ra else "",
                ra.effective_band if ra else "",
                ra.validation_status if ra else "",
                s.data_source,
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=shikshasetu_students.csv"},
    )


@router.get("/{student_id}")
def get_student_profile(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    st = _get_authorized_students(db, current_user).filter(Student.id == student_id.upper()).first()
    if not st:
        raise HTTPException(status_code=404, detail="Student record not found or outside authorized scope.")

    att_history = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.student_id == st.id)
        .order_by(AttendanceRecord.record_date.asc())
        .all()
    )
    acad_history = (
        db.query(AcademicRecord)
        .filter(AcademicRecord.student_id == st.id)
        .order_by(AcademicRecord.recorded_at.asc())
        .all()
    )
    risk_history = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.student_id == st.id)
        .order_by(RiskAssessment.created_at.desc())
        .all()
    )
    interventions = (
        db.query(Intervention)
        .options(joinedload(Intervention.outcomes), joinedload(Intervention.worker))
        .filter(Intervention.student_id == st.id)
        .order_by(Intervention.scheduled_date.desc())
        .all()
    )

    # Minimum necessary info for outreach workers
    is_outreach = current_user.role_obj.name == "outreach"

    return {
        "student": {
            "id": st.id,
            "school_id": st.school_id,
            "school_name": st.school.name if st.school else f"School {st.school_id}",
            "grade_level": st.grade_level,
            "enrollment_status": st.enrollment_status,
            "attendance_pct": st.attendance_pct,
            "previous_term_score": None if is_outreach else st.previous_term_score,
            "distance_km": st.distance_km,
            "prior_intervention_count": st.prior_intervention_count,
            "teacher_observations": None if is_outreach else st.teacher_observations,
            "is_synthetic_assessment": st.is_synthetic_assessment,
            "data_source": st.data_source,
        },
        "attendance_history": [
            {
                "week_label": a.week_label,
                "record_date": a.record_date.isoformat(),
                "attendance_pct": a.attendance_pct,
                "days_present": a.days_present,
                "days_scheduled": a.days_scheduled,
                "data_source": a.data_source,
            }
            for a in att_history
        ],
        "academic_history": []
        if is_outreach
        else [
            {
                "term": ac.term,
                "assessment_type": ac.assessment_type,
                "score": ac.score,
                "max_score": ac.max_score,
                "data_source": ac.data_source,
            }
            for ac in acad_history
        ],
        "risk_history": [
            {
                "id": r.id,
                "version": r.version,
                "priority_score": r.priority_score,
                "computed_band": r.computed_band,
                "effective_band": r.effective_band,
                "component_scores": r.component_scores,
                "contributing_factors": r.contributing_factors,
                "reason_codes": r.reason_codes,
                "missing_data_flags": r.missing_data_flags,
                "recommended_next_step": r.recommended_next_step,
                "validation_status": r.validation_status,
                "override_reason": r.override_reason,
                "is_current": r.is_current,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in risk_history
        ],
        "interventions": [
            {
                "id": iv.id,
                "intervention_type": iv.intervention_type,
                "worker_id": iv.worker_id,
                "worker_name": iv.worker.name if iv.worker else None,
                "scheduled_date": iv.scheduled_date.isoformat(),
                "status": iv.status,
                "approval_status": iv.approval_status,
                "pre_attendance_pct": iv.pre_attendance_pct,
                "post_attendance_pct": iv.post_attendance_pct,
                "teacher_notes": iv.teacher_notes,
                "outcomes": [
                    {
                        "id": o.id,
                        "outcome_category": o.outcome_category,
                        "visit_completed": o.visit_completed,
                        "agreed_next_step": o.agreed_next_step,
                        "follow_up_required": o.follow_up_required,
                        "follow_up_date": o.follow_up_date.isoformat() if o.follow_up_date else None,
                        "follow_up_completed": o.follow_up_completed,
                        "subsequent_attendance_pct": o.subsequent_attendance_pct,
                        "notes": o.notes,
                    }
                    for o in iv.outcomes
                ],
            }
            for iv in interventions
        ],
    }


@router.patch("/{student_id}/observations")
def update_teacher_observations(
    student_id: str,
    payload: ObservationUpdateRequest,
    current_user: User = Depends(require_roles("admin", "teacher")),
    db: Session = Depends(get_db),
):
    st = db.query(Student).filter(Student.id == student_id.upper()).first()
    if not st:
        raise HTTPException(status_code=404, detail="Student not found.")
    if current_user.role_obj.name == "teacher" and current_user.assigned_school_id not in (None, st.school_id):
        raise HTTPException(status_code=403, detail="Cannot edit observations for another school.")

    st.teacher_observations = payload.teacher_observations
    log_audit_event(
        db,
        actor=current_user,
        action="update_teacher_observation",
        record_type="student",
        record_id=st.id,
    )
    db.commit()
    return {"message": "Teacher observation updated.", "student_id": st.id}
