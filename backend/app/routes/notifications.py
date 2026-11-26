from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database import get_db
from app.models.entities import Notification, User

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("")
def list_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    role_name = current_user.role_obj.name
    items = (
        db.query(Notification)
        .filter(
            or_(
                Notification.user_id == current_user.id,
                Notification.target_role == role_name,
                Notification.target_role.is_(None),
            )
        )
        .order_by(Notification.is_read.asc(), Notification.created_at.desc())
        .limit(30)
        .all()
    )
    unread_count = sum(1 for n in items if not n.is_read)
    return {
        "unread_count": unread_count,
        "notifications": [
            {
                "id": n.id,
                "category": n.category,
                "severity": n.severity,
                "title": n.title,
                "message": n.message,
                "reference_type": n.reference_type,
                "reference_id": n.reference_id,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in items
        ],
    }


@router.post("/{notification_id}/read")
def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    n = db.query(Notification).filter(Notification.id == notification_id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found.")
    n.is_read = True
    db.commit()
    return {"message": "Notification marked as read."}


@router.post("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    role_name = current_user.role_obj.name
    db.query(Notification).filter(
        or_(
            Notification.user_id == current_user.id,
            Notification.target_role == role_name,
            Notification.target_role.is_(None),
        )
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return {"message": "All notifications marked as read."}
