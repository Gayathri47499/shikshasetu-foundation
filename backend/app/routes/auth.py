from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.auth.security import (
    create_access_token,
    generate_reset_token,
    get_current_user,
    hash_password,
    log_audit_event,
    verify_password,
)
from app.database import get_db
from app.models.entities import User
from app.schemas.api import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserProfile,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _to_user_profile(user: User) -> UserProfile:
    return UserProfile(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role_obj.name,
        role_display=user.role_obj.display_name,
        assigned_school_id=user.assigned_school_id,
        assigned_worker_id=user.assigned_worker_id,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .options(joinedload(User.role_obj))
        .filter(User.email == payload.email.lower().strip(), User.is_active.is_(True))
        .first()
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(user)
    log_audit_event(db, actor=user, action="user_login", record_type="user", record_id=str(user.id))
    db.commit()

    return TokenResponse(access_token=token, user=_to_user_profile(user))


@router.get("/me", response_model=UserProfile)
def get_me(current_user: User = Depends(get_current_user)):
    return _to_user_profile(current_user)


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user:
        # Return neutral message to prevent email enumeration
        return {
            "message": "If an account exists for that email, a password reset token has been generated.",
            "dev_reset_token": None,
        }

    token = generate_reset_token()
    user.reset_token = token
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(minutes=30)
    db.commit()

    return {
        "message": "Password reset instructions generated. Use the reset token below in development mode (or email service in production).",
        "dev_reset_token": token,
    }


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).options(joinedload(User.role_obj)).filter(User.reset_token == payload.token).first()
    if not user or not user.reset_token_expires:
        raise HTTPException(status_code=400, detail="Invalid or expired password reset token.")

    exp = user.reset_token_expires
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Password reset token has expired.")

    user.password_hash = hash_password(payload.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    log_audit_event(db, actor=user, action="password_reset", record_type="user", record_id=str(user.id))
    db.commit()
    return {"message": "Password updated successfully. You may now sign in."}


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log_audit_event(db, actor=current_user, action="user_logout", record_type="user", record_id=str(current_user.id))
    db.commit()
    return {"message": "Logged out successfully."}
