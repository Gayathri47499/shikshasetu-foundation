from datetime import datetime, date, timezone
from typing import Optional, List
from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Date,
    Text,
    ForeignKey,
    JSON,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    users: Mapped[List["User"]] = relationship("User", back_populates="role_obj")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    assigned_school_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("schools.id"), nullable=True
    )
    assigned_worker_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    auth_subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    reset_token: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    reset_token_expires: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    role_obj: Mapped["Role"] = relationship("Role", back_populates="users")
    assigned_school: Mapped[Optional["School"]] = relationship(
        "School", foreign_keys=[assigned_school_id]
    )


class School(Base):
    __tablename__ = "schools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # 1..10 matching Dataset A1
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    district: Mapped[str] = mapped_column(String(100), default="Rural & Semi-Urban Cluster", nullable=False)
    enrolled_students: Mapped[int] = mapped_column(Integer, nullable=False)
    baseline_attendance_pct: Mapped[float] = mapped_column(Float, nullable=False)
    coordinator_name: Mapped[str] = mapped_column(String(120), default="Designated Coordinator", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    data_source: Mapped[str] = mapped_column(String(60), default="veltris_assessment_a1", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        CheckConstraint("enrolled_students >= 0", name="ck_school_enrolled_nonneg"),
        CheckConstraint(
            "baseline_attendance_pct >= 0 AND baseline_attendance_pct <= 100",
            name="ck_school_att_range",
        ),
    )

    students: Mapped[List["Student"]] = relationship("Student", back_populates="school")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # e.g. ST001..ST012
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), nullable=False, index=True)
    grade_level: Mapped[str] = mapped_column(String(30), default="Grade 7", nullable=False)
    enrollment_status: Mapped[str] = mapped_column(String(30), default="enrolled", nullable=False)
    attendance_pct: Mapped[float] = mapped_column(Float, nullable=False)
    previous_term_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    distance_km: Mapped[float] = mapped_column(Float, nullable=False)
    prior_intervention_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    teacher_observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_synthetic_assessment: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    data_source: Mapped[str] = mapped_column(String(60), default="veltris_assessment_a2", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        CheckConstraint("attendance_pct >= 0 AND attendance_pct <= 100", name="ck_student_att_range"),
        CheckConstraint("distance_km >= 0", name="ck_student_distance_nonneg"),
        CheckConstraint("prior_intervention_count >= 0", name="ck_student_prior_int_nonneg"),
    )

    school: Mapped["School"] = relationship("School", back_populates="students")
    attendance_records: Mapped[List["AttendanceRecord"]] = relationship(
        "AttendanceRecord", back_populates="student", cascade="all, delete-orphan"
    )
    academic_records: Mapped[List["AcademicRecord"]] = relationship(
        "AcademicRecord", back_populates="student", cascade="all, delete-orphan"
    )
    risk_assessments: Mapped[List["RiskAssessment"]] = relationship(
        "RiskAssessment", back_populates="student", cascade="all, delete-orphan"
    )
    interventions: Mapped[List["Intervention"]] = relationship(
        "Intervention", back_populates="student", cascade="all, delete-orphan"
    )


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), nullable=False, index=True)
    week_label: Mapped[str] = mapped_column(String(30), nullable=False)  # e.g. "2026-W44"
    record_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    attendance_pct: Mapped[float] = mapped_column(Float, nullable=False)
    days_present: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    days_scheduled: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    consecutive_absences: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    data_source: Mapped[str] = mapped_column(String(60), default="veltris_assessment_a2", nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        CheckConstraint("attendance_pct >= 0 AND attendance_pct <= 100", name="ck_att_rec_range"),
        Index("ix_att_student_date", "student_id", "record_date"),
    )

    student: Mapped["Student"] = relationship("Student", back_populates="attendance_records")


class AcademicRecord(Base):
    __tablename__ = "academic_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    term: Mapped[str] = mapped_column(String(40), nullable=False)
    assessment_type: Mapped[str] = mapped_column(String(60), default="Term Examination", nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    data_source: Mapped[str] = mapped_column(String(60), default="veltris_assessment_a2", nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="ck_acad_score_range"),
    )

    student: Mapped["Student"] = relationship("Student", back_populates="academic_records")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    priority_score: Mapped[float] = mapped_column(Float, nullable=False)
    computed_band: Mapped[str] = mapped_column(String(30), nullable=False)  # High Priority / Review Soon / Routine Review
    effective_band: Mapped[str] = mapped_column(String(30), nullable=False)
    component_scores: Mapped[dict] = mapped_column(JSON, nullable=False)
    contributing_factors: Mapped[list] = mapped_column(JSON, nullable=False)
    reason_codes: Mapped[list] = mapped_column(JSON, nullable=False)
    missing_data_flags: Mapped[list] = mapped_column(JSON, nullable=False)
    recommended_next_step: Mapped[str] = mapped_column(Text, nullable=False)
    validation_status: Mapped[str] = mapped_column(
        String(30), default="pending_review", nullable=False
    )  # pending_review | validated | overridden | deferred
    override_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    student: Mapped["Student"] = relationship("Student", back_populates="risk_assessments")
    reviewed_by: Mapped[Optional["User"]] = relationship("User")


class OutreachWorker(Base):
    __tablename__ = "outreach_workers"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # OW01..OW05
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    cluster_schools: Mapped[list] = mapped_column(JSON, nullable=False)  # e.g. [1, 2]
    max_daily_visits: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    working_days_per_week: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    interventions: Mapped[List["Intervention"]] = relationship("Intervention", back_populates="worker")
    visit_schedules: Mapped[List["VisitSchedule"]] = relationship("VisitSchedule", back_populates="worker")


class Intervention(Base):
    __tablename__ = "interventions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), nullable=False, index=True)
    worker_id: Mapped[Optional[str]] = mapped_column(ForeignKey("outreach_workers.id"), nullable=True)
    intervention_type: Mapped[str] = mapped_column(
        String(60), default="Household Visit", nullable=False
    )  # Household Visit | School Counseling | Family Check-in | Transport Support Review
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(30), default="pending", nullable=False
    )  # proposed | pending | completed | cancelled | rescheduled
    approval_status: Mapped[str] = mapped_column(
        String(30), default="approved", nullable=False
    )  # proposed | approved | rejected
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    estimated_cost_inr: Mapped[float] = mapped_column(Float, default=250.0, nullable=False)
    pre_attendance_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    post_attendance_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    teacher_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_source: Mapped[str] = mapped_column(String(60), default="platform_workflow", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    student: Mapped["Student"] = relationship("Student", back_populates="interventions")
    worker: Mapped[Optional["OutreachWorker"]] = relationship("OutreachWorker", back_populates="interventions")
    outcomes: Mapped[List["InterventionOutcome"]] = relationship(
        "InterventionOutcome", back_populates="intervention", cascade="all, delete-orphan"
    )


class InterventionOutcome(Base):
    __tablename__ = "intervention_outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    intervention_id: Mapped[int] = mapped_column(ForeignKey("interventions.id"), nullable=False, index=True)
    outcome_category: Mapped[str] = mapped_column(
        String(60), nullable=False
    )  # Contacted - Support Plan Agreed | Family Unavailable | Transport Barrier Identified | Health/Financial Referral | Attendance Stabilizing
    visit_completed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    agreed_next_step: Mapped[str] = mapped_column(Text, nullable=False)
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    follow_up_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    follow_up_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    subsequent_attendance_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    intervention: Mapped["Intervention"] = relationship("Intervention", back_populates="outcomes")


class VisitSchedule(Base):
    __tablename__ = "visit_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    week_start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    visit_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    worker_id: Mapped[str] = mapped_column(ForeignKey("outreach_workers.id"), nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), nullable=False)
    intervention_id: Mapped[Optional[int]] = mapped_column(ForeignKey("interventions.id"), nullable=True)
    priority_score_snapshot: Mapped[float] = mapped_column(Float, nullable=False)
    priority_band_snapshot: Mapped[str] = mapped_column(String(30), nullable=False)
    approval_status: Mapped[str] = mapped_column(
        String(30), default="proposed", nullable=False
    )  # proposed | approved | rejected
    visit_status: Mapped[str] = mapped_column(
        String(30), default="pending", nullable=False
    )  # pending | completed | cancelled | rescheduled
    estimated_cost_inr: Mapped[float] = mapped_column(Float, default=250.0, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    worker: Mapped["OutreachWorker"] = relationship("OutreachWorker", back_populates="visit_schedules")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    target_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # review_recommendation | pending_validation | upcoming_visit | overdue_followup | failed_upload | weekly_summary
    severity: Mapped[str] = mapped_column(String(20), default="info", nullable=False)  # info | warning | urgent | success
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    actor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    record_type: Mapped[str] = mapped_column(String(50), nullable=False)
    record_id: Mapped[str] = mapped_column(String(60), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    valid_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    error_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)  # previewed | imported | failed
    errors_summary: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    uploaded_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AssistantMessage(Base):
    __tablename__ = "assistant_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    verified_facts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    provider_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
