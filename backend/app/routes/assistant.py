from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.ai.assistant_service import ask_teacher_assistant
from app.auth.security import get_current_user, log_audit_event
from app.config import get_settings
from app.database import get_db
from app.models.entities import AssistantMessage, User
from app.schemas.api import AssistantAskRequest

router = APIRouter(prefix="/api/assistant", tags=["AI Teacher Assistant"])
settings = get_settings()


@router.get("/status")
def assistant_status(current_user: User = Depends(get_current_user)):
    return {
        "gemini_configured": bool(settings.GEMINI_API_KEY.strip()),
        "model": settings.GEMINI_MODEL,
        "pii_protection": "Student IDs only; names/addresses never transmitted to external LLM.",
        "human_in_the_loop": True,
    }


@router.get("/history")
def get_history(
    session_id: str = Query("default-session"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    msgs = (
        db.query(AssistantMessage)
        .filter(AssistantMessage.session_id == session_id, AssistantMessage.user_id == current_user.id)
        .order_by(AssistantMessage.created_at.asc())
        .all()
    )
    return {
        "session_id": session_id,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "provider_used": m.provider_used,
                "verified_facts": m.verified_facts,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in msgs
        ],
    }


@router.post("/ask")
async def ask_assistant(
    payload: AssistantAskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = await ask_teacher_assistant(
        db=db,
        user=current_user,
        question=payload.question,
        session_id=payload.session_id,
    )
    log_audit_event(
        db,
        actor=current_user,
        action="ai_assistant_query",
        record_type="assistant",
        record_id=payload.session_id,
    )
    db.commit()
    return result
