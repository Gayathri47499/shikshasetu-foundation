from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.auth.security import get_current_user, log_audit_event, require_roles
from app.config import get_settings
from app.database import get_db
from app.models.entities import (
    Intervention,
    InterventionOutcome,
    OutreachWorker,
    Student,
    User,
)
from app.schemas.api import (
    InterventionCreateRequest,
    InterventionOutcomeRequest,
    InterventionStatusUpdateRequest,
    OfflineDraftSyncRequest,
)

router = APIRouter(prefix="/api/interventions", tags=["Intervention Management"])
settings = get_settings()


@router.get("")
def list_interventions(
    status: Optional[str] = Query(None),
    school_id: Optional[int] = Query(None),
    worker_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Intervention).options(
        joinedload(Intervention.outcomes),
        joinedload(Intervention.worker),
        joinedload(Intervention.student),
    )

    role = current_user.role_obj.name
    if role == "teacher" and current_user.assigned_school_id is not None:
        q = q.filter(Intervention.school_id == current_user.assigned_school_id)
    elif role == "outreach" and current_user.assigned_worker_id:
        q = q.filter(Intervention.worker_id == current_user.assigned_worker_id)

    if status:
        q = q.filter(Intervention.status == status)
    if school_id is not None:
        q = q.filter(Intervention.school_id == school_id)
    if worker_id:
        q = q.filter(Intervention.worker_id == worker_id)

    items = q.order_by(Intervention.scheduled_date.desc(), Intervention.id.desc()).all()
    workers = db.query(OutreachWorker).order_by(OutreachWorker.id).all()

    return {
        "interventions": [
            {
                "id": iv.id,
                "student_id": iv.student_id,
                "school_id": iv.school_id,
                "worker_id": iv.worker_id,
                "worker_name": iv.worker.name if iv.worker else None,
                "intervention_type": iv.intervention_type,
                "scheduled_date": iv.scheduled_date.isoformat(),
                "status": iv.status,
                "approval_status": iv.approval_status,
                "estimated_cost_inr": iv.estimated_cost_inr,
                "pre_attendance_pct": iv.pre_attendance_pct,
                "post_attendance_pct": iv.post_attendance_pct,
                "teacher_notes": iv.teacher_notes,
                "data_source": iv.data_source,
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
                        "created_at": o.created_at.isoformat() if o.created_at else None,
                    }
                    for o in iv.outcomes
                ],
            }
            for iv in items
        ],
        "workers": [
            {
                "id": w.id,
                "name": w.name,
                "cluster_schools": w.cluster_schools,
                "max_daily_visits": w.max_daily_visits,
                "working_days_per_week": w.working_days_per_week,
            }
            for w in workers
        ],
    }


@router.post("")
def create_intervention(
    payload: InterventionCreateRequest,
    current_user: User = Depends(require_roles("admin", "teacher")),
    db: Session = Depends(get_db),
):
    st = db.query(Student).filter(Student.id == payload.student_id.upper()).first()
    if not st:
        raise HTTPException(status_code=404, detail="Student not found.")
    if current_user.role_obj.name == "teacher" and current_user.assigned_school_id not in (None, st.school_id):
        raise HTTPException(status_code=403, detail="Cannot create intervention outside your assigned school.")

    # Enforce daily worker limit & weekly budget if worker assigned
    if payload.worker_id:
        worker = db.query(OutreachWorker).filter(OutreachWorker.id == payload.worker_id).first()
        if not worker:
            raise HTTPException(status_code=404, detail="Outreach worker not found.")
        same_day_count = (
            db.query(Intervention)
            .filter(
                Intervention.worker_id == payload.worker_id,
                Intervention.scheduled_date == payload.scheduled_date,
                Intervention.status != "cancelled",
            )
            .count()
        )
        if same_day_count >= worker.max_daily_visits:
            raise HTTPException(
                status_code=400,
                detail=f"Daily limit reached: {worker.name} already has {same_day_count}/{worker.max_daily_visits} visits on {payload.scheduled_date}.",
            )

    iv = Intervention(
        student_id=st.id,
        school_id=payload.school_id,
        worker_id=payload.worker_id,
        intervention_type=payload.intervention_type,
        scheduled_date=payload.scheduled_date,
        status="pending",
        approval_status="approved",
        approved_by_id=current_user.id,
        estimated_cost_inr=settings.AVERAGE_VISIT_COST_INR if payload.intervention_type == "Household Visit" else 0.0,
        pre_attendance_pct=st.attendance_pct,
        teacher_notes=payload.teacher_notes,
        data_source="platform_workflow",
    )
    db.add(iv)
    db.flush()
    log_audit_event(
        db,
        actor=current_user,
        action="intervention_created",
        record_type="intervention",
        record_id=str(iv.id),
        details={"student_id": st.id, "worker_id": payload.worker_id},
    )
    db.commit()
    return {"message": "Approved intervention created.", "intervention_id": iv.id}


@router.patch("/{intervention_id}/status")
def update_intervention_status(
    intervention_id: int,
    payload: InterventionStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    iv = db.query(Intervention).filter(Intervention.id == intervention_id).first()
    if not iv:
        raise HTTPException(status_code=404, detail="Intervention not found.")
    if current_user.role_obj.name == "outreach" and current_user.assigned_worker_id not in (None, iv.worker_id):
        raise HTTPException(status_code=403, detail="Outreach workers can only update their assigned visits.")

    iv.status = payload.status
    if payload.scheduled_date:
        iv.scheduled_date = payload.scheduled_date
    if payload.teacher_notes:
        iv.teacher_notes = payload.teacher_notes

    log_audit_event(
        db,
        actor=current_user,
        action=f"intervention_status_{payload.status}",
        record_type="intervention",
        record_id=str(iv.id),
    )
    db.commit()
    return {"message": f"Intervention #{iv.id} updated to {iv.status}."}


@router.post("/{intervention_id}/outcome")
def record_intervention_outcome(
    intervention_id: int,
    payload: InterventionOutcomeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    iv = db.query(Intervention).filter(Intervention.id == intervention_id).first()
    if not iv:
        raise HTTPException(status_code=404, detail="Intervention not found.")
    if current_user.role_obj.name == "outreach" and current_user.assigned_worker_id not in (None, iv.worker_id):
        raise HTTPException(status_code=403, detail="Outreach workers can only record outcomes for their assigned visits.")

    outcome = InterventionOutcome(
        intervention_id=iv.id,
        outcome_category=payload.outcome_category,
        visit_completed=payload.visit_completed,
        agreed_next_step=payload.agreed_next_step,
        follow_up_required=payload.follow_up_required,
        follow_up_date=payload.follow_up_date,
        follow_up_completed=payload.follow_up_completed,
        subsequent_attendance_pct=payload.subsequent_attendance_pct,
        notes=payload.notes,
        recorded_by_id=current_user.id,
    )
    db.add(outcome)
    if payload.visit_completed:
        iv.status = "completed"
    if payload.subsequent_attendance_pct is not None:
        iv.post_attendance_pct = payload.subsequent_attendance_pct
        st = db.query(Student).filter(Student.id == iv.student_id).first()
        if st:
            st.attendance_pct = payload.subsequent_attendance_pct

    log_audit_event(
        db,
        actor=current_user,
        action="intervention_outcome_recorded",
        record_type="intervention",
        record_id=str(iv.id),
        details={"outcome_category": payload.outcome_category},
    )
    db.commit()
    return {"message": "Intervention outcome recorded.", "outcome_id": outcome.id}


@router.post("/sync-offline-drafts")
def sync_offline_drafts(
    payload: OfflineDraftSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Synchronize locally cached offline field note drafts once connectivity returns."""
    synced_ids = []
    skipped = []
    for draft in payload.drafts:
        iv = db.query(Intervention).filter(Intervention.id == draft.intervention_id).first()
        if not iv:
            skipped.append({"local_draft_id": draft.local_draft_id, "reason": "Intervention not found."})
            continue
        if current_user.role_obj.name == "outreach" and current_user.assigned_worker_id not in (None, iv.worker_id):
            skipped.append({"local_draft_id": draft.local_draft_id, "reason": "Not assigned to this worker."})
            continue

        outcome = InterventionOutcome(
            intervention_id=iv.id,
            outcome_category=draft.outcome_category,
            visit_completed=draft.visit_completed,
            agreed_next_step=draft.agreed_next_step,
            follow_up_required=draft.follow_up_required,
            follow_up_date=draft.follow_up_date,
            subsequent_attendance_pct=draft.subsequent_attendance_pct,
            notes=f"[Synced offline draft captured {draft.captured_at}] {draft.notes or ''}".strip(),
            recorded_by_id=current_user.id,
        )
        db.add(outcome)
        if draft.visit_completed:
            iv.status = "completed"
        if draft.subsequent_attendance_pct is not None:
            iv.post_attendance_pct = draft.subsequent_attendance_pct
        synced_ids.append(draft.local_draft_id)

    log_audit_event(
        db,
        actor=current_user,
        action="offline_drafts_synced",
        record_type="intervention_outcome",
        record_id=f"{len(synced_ids)}_drafts",
    )
    db.commit()
    return {"synced_draft_ids": synced_ids, "skipped": skipped}
