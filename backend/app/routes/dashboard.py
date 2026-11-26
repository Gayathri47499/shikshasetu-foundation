from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.analytics.kpi_engine import compute_dashboard_summary
from app.auth.security import get_current_user
from app.database import get_db
from app.models.entities import AuditEvent, User

router = APIRouter(prefix="/api/dashboard", tags=["Foundation Dashboard"])


@router.get("")
def get_dashboard(
    school_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed_school = current_user.assigned_school_id if current_user.role_obj.name == "teacher" else None
    summary = compute_dashboard_summary(
        db=db,
        school_id=school_id,
        date_from=date_from,
        date_to=date_to,
        allowed_school_id=allowed_school,
    )

    recent_events = (
        db.query(AuditEvent)
        .order_by(AuditEvent.created_at.desc())
        .limit(10)
        .all()
    )
    summary["recent_activities"] = [
        {
            "id": e.id,
            "actor_email": e.actor_email,
            "actor_role": e.actor_role,
            "action": e.action,
            "record_type": e.record_type,
            "record_id": e.record_id,
            "reason": e.reason,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in recent_events
    ]
    return summary
