from dataclasses import asdict
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.auth.security import get_current_user, log_audit_event, require_roles
from app.database import get_db
from app.intelligence.risk_engine import DEFAULT_CONFIG, evaluate_student_priority
from app.models.entities import Intervention, RiskAssessment, Student, User
from app.schemas.api import RiskReviewRequest

router = APIRouter(prefix="/api/risk", tags=["Student Risk Intelligence"])


@router.get("/review-queue")
def get_review_queue(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Student).options(joinedload(Student.school))
    if current_user.role_obj.name == "teacher" and current_user.assigned_school_id is not None:
        q = q.filter(Student.school_id == current_user.assigned_school_id)
    students = q.all()
    student_map = {s.id: s for s in students}

    assessments = (
        db.query(RiskAssessment)
        .options(joinedload(RiskAssessment.reviewed_by))
        .filter(RiskAssessment.is_current.is_(True))
        .all()
    )

    queue = []
    for a in assessments:
        st = student_map.get(a.student_id)
        if not st:
            continue
        queue.append(
            {
                "assessment_id": a.id,
                "student_id": st.id,
                "school_id": st.school_id,
                "school_name": st.school.name if st.school else f"School {st.school_id}",
                "attendance_pct": st.attendance_pct,
                "previous_term_score": st.previous_term_score,
                "distance_km": st.distance_km,
                "prior_intervention_count": st.prior_intervention_count,
                "priority_score": a.priority_score,
                "computed_band": a.computed_band,
                "effective_band": a.effective_band,
                "component_scores": a.component_scores,
                "contributing_factors": a.contributing_factors,
                "reason_codes": a.reason_codes,
                "missing_data_flags": a.missing_data_flags,
                "recommended_next_step": a.recommended_next_step,
                "validation_status": a.validation_status,
                "override_reason": a.override_reason,
                "reviewed_by_name": a.reviewed_by.full_name if a.reviewed_by else None,
                "reviewed_at": a.reviewed_at.isoformat() if a.reviewed_at else None,
                "is_synthetic_assessment": st.is_synthetic_assessment,
            }
        )

    queue.sort(key=lambda item: -item["priority_score"])
    return {
        "queue": queue,
        "scoring_config": asdict(DEFAULT_CONFIG),
        "methodology_disclaimer": (
            "Operational triage only. Dataset A2 contains 12 synthetic student records with no verified dropout labels; "
            "no supervised dropout prediction model is claimed or trained on these records."
        ),
    }


@router.post("/recalculate")
def recalculate_risk_scores(
    current_user: User = Depends(require_roles("admin", "teacher")),
    db: Session = Depends(get_db),
):
    q = db.query(Student)
    if current_user.role_obj.name == "teacher" and current_user.assigned_school_id is not None:
        q = q.filter(Student.school_id == current_user.assigned_school_id)
    students = q.all()

    updated = 0
    for st in students:
        # Count completed visits that still lack any documented outcome
        completed_ints = (
            db.query(Intervention)
            .options(joinedload(Intervention.outcomes))
            .filter(Intervention.student_id == st.id, Intervention.status == "completed")
            .all()
        )
        pending_outcome_cnt = sum(1 for iv in completed_ints if len(iv.outcomes) == 0)

        eval_res = evaluate_student_priority(
            student_id=st.id,
            attendance_pct=st.attendance_pct,
            previous_term_score=st.previous_term_score,
            distance_km=st.distance_km,
            prior_intervention_count=st.prior_intervention_count,
            pending_outcome_review_count=pending_outcome_cnt,
        )

        prev_current = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.student_id == st.id, RiskAssessment.is_current.is_(True))
            .all()
        )
        next_version = max((p.version for p in prev_current), default=0) + 1
        for p in prev_current:
            p.is_current = False

        db.add(
            RiskAssessment(
                student_id=st.id,
                version=next_version,
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
        updated += 1

    log_audit_event(
        db,
        actor=current_user,
        action="risk_recalculated",
        record_type="risk_assessment",
        record_id=f"{updated}_students",
    )
    db.commit()
    return {"message": f"Recalculated transparent priority indicators for {updated} student(s).", "updated_count": updated}


@router.post("/{student_id}/review")
def review_or_override_risk(
    student_id: str,
    payload: RiskReviewRequest,
    current_user: User = Depends(require_roles("admin", "teacher")),
    db: Session = Depends(get_db),
):
    st = db.query(Student).filter(Student.id == student_id.upper()).first()
    if not st:
        raise HTTPException(status_code=404, detail="Student not found.")
    if current_user.role_obj.name == "teacher" and current_user.assigned_school_id not in (None, st.school_id):
        raise HTTPException(status_code=403, detail="Teachers can only review students in their assigned school.")

    ra = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.student_id == st.id, RiskAssessment.is_current.is_(True))
        .first()
    )
    if not ra:
        raise HTTPException(status_code=404, detail="Current risk assessment not found.")

    ra.validation_status = payload.validation_status
    if payload.validation_status == "overridden" and payload.effective_band:
        ra.effective_band = payload.effective_band
    elif payload.validation_status == "validated":
        ra.effective_band = ra.computed_band

    ra.override_reason = payload.override_reason
    ra.reviewed_by_id = current_user.id
    ra.reviewed_at = datetime.now(timezone.utc)

    log_audit_event(
        db,
        actor=current_user,
        action=f"risk_{payload.validation_status}",
        record_type="risk_assessment",
        record_id=st.id,
        reason=payload.override_reason,
        details={"computed_band": ra.computed_band, "effective_band": ra.effective_band},
    )
    db.commit()

    return {
        "message": f"Risk assessment for {st.id} marked as {payload.validation_status}.",
        "student_id": st.id,
        "effective_band": ra.effective_band,
        "validation_status": ra.validation_status,
    }
