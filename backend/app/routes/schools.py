from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database import get_db
from app.models.entities import AttendanceRecord, Intervention, RiskAssessment, School, Student, User

router = APIRouter(prefix="/api/schools", tags=["School Analytics"])


@router.get("")
def list_schools(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(School).order_by(School.baseline_attendance_pct.asc())
    if current_user.role_obj.name == "teacher" and current_user.assigned_school_id is not None:
        q = q.filter(School.id == current_user.assigned_school_id)
    schools = q.all()

    students = db.query(Student).all()
    assessments = {
        a.student_id: a
        for a in db.query(RiskAssessment).filter(RiskAssessment.is_current.is_(True)).all()
    }

    ranked = sorted(schools, key=lambda s: -s.baseline_attendance_pct)
    rank_lookup = {s.id: idx + 1 for idx, s in enumerate(ranked)}

    items = []
    for sc in schools:
        sc_students = [s for s in students if s.school_id == sc.id]
        high_cnt = sum(
            1
            for s in sc_students
            if assessments.get(s.id) and assessments[s.id].effective_band == "High Priority"
        )
        review_cnt = sum(
            1
            for s in sc_students
            if assessments.get(s.id) and assessments[s.id].effective_band == "Review Soon"
        )
        items.append(
            {
                "id": sc.id,
                "code": sc.code,
                "name": sc.name,
                "district": sc.district,
                "enrolled_students": sc.enrolled_students,
                "baseline_attendance_pct": sc.baseline_attendance_pct,
                "coordinator_name": sc.coordinator_name,
                "status": sc.status,
                "attendance_rank": rank_lookup.get(sc.id),
                "requires_attention": sc.baseline_attendance_pct < 70.0,
                "tracked_sample_students": len(sc_students),
                "high_priority_count": high_cnt,
                "review_soon_count": review_cnt,
                "data_source": sc.data_source,
            }
        )

    total_enrolled = sum(s.enrolled_students for s in schools)
    weighted_avg = (
        round(sum(s.enrolled_students * s.baseline_attendance_pct for s in schools) / total_enrolled, 2)
        if total_enrolled > 0
        else 0.0
    )

    return {
        "schools": items,
        "summary": {
            "total_schools": len(schools),
            "total_enrolled_students": total_enrolled,
            "weighted_average_attendance_pct": weighted_avg,
            "schools_below_70_pct": sum(1 for s in schools if s.baseline_attendance_pct < 70.0),
        },
    }


@router.get("/{school_id}")
def get_school_detail(
    school_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role_obj.name == "teacher" and current_user.assigned_school_id not in (None, school_id):
        raise HTTPException(status_code=403, detail="You can only view your assigned school.")

    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found.")

    students = db.query(Student).filter(Student.school_id == school_id).order_by(Student.id).all()
    assessments = {
        a.student_id: a
        for a in db.query(RiskAssessment).filter(RiskAssessment.is_current.is_(True)).all()
    }
    att_rows = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.school_id == school_id)
        .order_by(AttendanceRecord.record_date.asc())
        .all()
    )
    weekly_map = {}
    for r in att_rows:
        weekly_map.setdefault(r.week_label, []).append(r.attendance_pct)
    weekly_trend = [
        {"week": wk, "avg_attendance_pct": round(sum(v) / len(v), 2)}
        for wk, v in weekly_map.items()
    ]

    interventions_count = db.query(Intervention).filter(Intervention.school_id == school_id).count()

    return {
        "school": {
            "id": school.id,
            "code": school.code,
            "name": school.name,
            "district": school.district,
            "enrolled_students": school.enrolled_students,
            "baseline_attendance_pct": school.baseline_attendance_pct,
            "coordinator_name": school.coordinator_name,
            "status": school.status,
            "interventions_count": interventions_count,
            "data_source": school.data_source,
        },
        "weekly_trend": weekly_trend,
        "students": [
            {
                "id": s.id,
                "grade_level": s.grade_level,
                "attendance_pct": s.attendance_pct,
                "previous_term_score": s.previous_term_score,
                "distance_km": s.distance_km,
                "prior_intervention_count": s.prior_intervention_count,
                "effective_band": assessments[s.id].effective_band if s.id in assessments else "Routine Review",
                "priority_score": assessments[s.id].priority_score if s.id in assessments else 0.0,
            }
            for s in students
        ],
    }
