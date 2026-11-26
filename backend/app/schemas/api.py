from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)


class UserProfile(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    role_display: str
    assigned_school_id: Optional[int] = None
    assigned_worker_id: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class ObservationUpdateRequest(BaseModel):
    teacher_observations: str = Field(..., max_length=2000)


class RiskReviewRequest(BaseModel):
    validation_status: str = Field(..., pattern="^(validated|overridden|deferred)$")
    effective_band: Optional[str] = Field(None, pattern="^(High Priority|Review Soon|Routine Review)$")
    override_reason: str = Field(..., min_length=3, max_length=1000)


class InterventionCreateRequest(BaseModel):
    student_id: str
    school_id: int
    worker_id: Optional[str] = None
    intervention_type: str = "Household Visit"
    scheduled_date: date
    teacher_notes: Optional[str] = None


class InterventionStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(pending|completed|cancelled|rescheduled)$")
    scheduled_date: Optional[date] = None
    teacher_notes: Optional[str] = None


class InterventionOutcomeRequest(BaseModel):
    outcome_category: str
    visit_completed: bool = True
    agreed_next_step: str = Field(..., min_length=3)
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None
    follow_up_completed: bool = False
    subsequent_attendance_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    notes: Optional[str] = None


class PlannerProposeRequest(BaseModel):
    week_start_date: date
    max_visits_to_propose: int = Field(15, ge=1, le=100)


class PlannerApprovalRequest(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected)$")
    notes: Optional[str] = None


class AssistantAskRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1500)
    session_id: str = Field(default="default-session", max_length=64)


class OfflineDraftSyncItem(BaseModel):
    local_draft_id: str
    intervention_id: int
    outcome_category: str
    visit_completed: bool = True
    agreed_next_step: str
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None
    subsequent_attendance_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    notes: Optional[str] = None
    captured_at: str


class OfflineDraftSyncRequest(BaseModel):
    drafts: List[OfflineDraftSyncItem]
