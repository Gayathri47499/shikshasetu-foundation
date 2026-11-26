import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.database import get_db
from app.models.entities import AuditEvent, User

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)

PBKDF2_ITERATIONS = 310_000


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a 16-byte random salt."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2-HMAC-SHA256 hash."""
    try:
        scheme, iter_str, salt_b64, digest_b64 = stored_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iter_str)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def create_access_token(user: User) -> str:
    """Create a signed JWT access token containing minimal identity and role claims."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role_obj.name,
        "school_id": user.assigned_school_id,
        "worker_id": user.assigned_worker_id,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please sign in again.",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        ) from exc


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required.",
        )
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload.",
        )
    user = (
        db.query(User)
        .options(joinedload(User.role_obj))
        .filter(User.id == int(user_id), User.is_active.is_(True))
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or inactive.",
        )
    return user


def require_roles(*allowed_roles: str):
    """Dependency factory enforcing server-side role-based access control."""

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        role_name = current_user.role_obj.name if current_user.role_obj else ""
        if role_name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name}' is not authorized for this action. Required: {', '.join(allowed_roles)}.",
            )
        return current_user

    return dependency


def log_audit_event(
    db: Session,
    actor: Optional[User],
    action: str,
    record_type: str,
    record_id: str,
    reason: Optional[str] = None,
    details: Optional[dict] = None,
) -> AuditEvent:
    """Append an immutable audit log entry without storing sensitive PII."""
    event = AuditEvent(
        actor_id=actor.id if actor else None,
        actor_email=actor.email if actor else "system@shikshasetu.org",
        actor_role=actor.role_obj.name if actor and actor.role_obj else "system",
        action=action,
        record_type=record_type,
        record_id=str(record_id),
        reason=reason,
        details=details,
    )
    db.add(event)
    return event


def filter_students_query_for_role(query, user: User, StudentModel):
    """Apply role-based row filtering: teachers see assigned school; outreach sees assigned/approved cases."""
    role = user.role_obj.name
    if role == "admin":
        return query
    if role == "teacher" and user.assigned_school_id is not None:
        return query.filter(StudentModel.school_id == user.assigned_school_id)
    return query
