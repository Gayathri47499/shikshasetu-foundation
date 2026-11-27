import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

import httpx
from sqlalchemy.orm import Session, joinedload

from app.analytics.kpi_engine import compute_dashboard_summary, compute_impact_kpis
from app.config import get_settings
from app.models.entities import (
    AssistantMessage,
    Intervention,
    RiskAssessment,
    School,
    Student,
    User,
)

settings = get_settings()
logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTIONS = """You are the ShikshaSetu Foundation AI Teacher Assistant.
Follow these strict rules:
1. Rely ONLY on the VERIFIED_BACKEND_FACTS JSON provided to you. Never invent student IDs, scores, attendance percentages, or outcomes.
2. Never claim a student will definitely drop out. Risk bands are operational review prompts only.
3. Never state that an intervention caused attendance improvement; describe before/after changes as descriptive associations only.
4. Keep language empathetic, respectful, and non-stigmatizing. Frame distance as a travel/access barrier, never low motivation.
5. Clearly separate two sections in your response:
   - **Verified Backend Facts** (citing exact IDs and numbers from the JSON)
   - **Suggested Teacher Next Steps (Requires Human Review)**
6. End with a brief reminder that final decisions remain with the Teacher Coordinator and Outreach Team."""


class BaseLLMProvider(ABC):
    """Provider abstraction so Gemini can be swapped without rewriting application logic."""

    provider_name: str = "base"

    @abstractmethod
    async def generate(self, question: str, verified_facts: Dict, history: List[Dict]) -> Tuple[str, str]:
        """Returns (response_text, provider_label)."""
        raise NotImplementedError


class DeterministicFallbackProvider(BaseLLMProvider):
    """Safe, grounded deterministic synthesizer used when GEMINI_API_KEY is absent or rate-limited."""

    provider_name = "deterministic-grounded-fallback"

    async def generate(self, question: str, verified_facts: Dict, history: List[Dict]) -> Tuple[str, str]:
        lines = ["**Verified Backend Facts**"]
        if "student" in verified_facts:
            st = verified_facts["student"]
            lines.append(
                f"- Student **{st['student_id']}** (School {st['school_id']}): Attendance **{st['attendance_pct']}%**, "
                f"Previous term score **{st['previous_term_score']}**, Distance **{st['distance_km']} km**, "
                f"Prior visits **{st['prior_intervention_count']}**."
            )
            if st.get("risk"):
                r = st["risk"]
                lines.append(
                    f"- Priority Band: **{r['effective_band']}** (Prototype Index **{r['priority_score']}/100**, "
                    f"Validation: `{r['validation_status']}`)."
                )
                lines.append(f"- Reason codes: {', '.join(r.get('reason_codes', []))}.")
        if "priority_students" in verified_facts:
            top = verified_facts["priority_students"][:5]
            lines.append("- Top prioritized students requiring review:")
            for item in top:
                lines.append(
                    f"  - **{item['student_id']}** (School {item['school_id']}): {item['attendance_pct']}% attendance, "
                    f"Score {item['previous_term_score']}, {item['distance_km']} km — Band: **{item['effective_band']}** ({item['priority_score']}/100)"
                )
        if "lowest_schools" in verified_facts:
            lines.append("- Schools with lowest baseline attendance:")
            for sc in verified_facts["lowest_schools"]:
                lines.append(
                    f"  - **{sc['name']}** ({sc['code']}): **{sc['attendance_pct']}%** attendance across {sc['enrolled_students']} enrolled students."
                )
        if "school_summary" in verified_facts:
            sc = verified_facts["school_summary"]
            lines.append(
                f"- **{sc['name']}**: {sc['enrolled_students']} enrolled students, baseline attendance **{sc['attendance_pct']}%**, "
                f"{sc['tracked_students_count']} tracked student sample profile(s)."
            )
        if "pending_followups" in verified_facts:
            pf = verified_facts["pending_followups"]
            lines.append(f"- Pending / due follow-up items: **{len(pf)}** record(s) found.")
            for item in pf[:5]:
                lines.append(
                    f"  - Intervention #{item['intervention_id']} ({item['student_id']}, {item['status']}): {item['note']}"
                )
        if "impact_summary" in verified_facts:
            imp = verified_facts["impact_summary"]
            lines.append(
                f"- Interventions: {imp['completed']} completed, {imp['pending']} pending, "
                f"{imp['improved_attendance_count']} with positive before/after attendance change (descriptive only)."
            )

        lines.append("")
        lines.append("**Suggested Teacher Next Steps (Requires Human Review)**")
        if "student" in verified_facts and verified_facts["student"].get("risk"):
            lines.append(f"- {verified_facts['student']['risk']['recommended_next_step']}")
        else:
            lines.append(
                "- Review the prioritized student indicators alongside teacher context before approving any outreach visit."
            )
            lines.append(
                "- Verify outcomes of prior household visits before scheduling repeat visits so worker capacity (max 100/week) is used effectively."
            )
        lines.append("")
        lines.append(
            "_Note: Generated by the grounded backend fallback engine (configure `GEMINI_API_KEY` in `backend/.env` for Gemini AI synthesis). "
            "All final student support decisions remain with the Teacher Coordinator._"
        )
        return "\n".join(lines), self.provider_name


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini API adapter via REST (httpx) with graceful fallback on errors/rate limits."""

    provider_name = "gemini-api"

    def __init__(self, api_key: str, model: str):
        cleaned_api_key = (api_key or "").strip().strip('"').strip("'")
        cleaned_model = (model or "gemini-3.5-flash").strip().strip('"').strip("'")
        if cleaned_model.startswith("models/"):
            cleaned_model = cleaned_model.removeprefix("models/")
        self.api_key = cleaned_api_key
        self.model = cleaned_model or "gemini-3.5-flash"
        self.fallback = DeterministicFallbackProvider()

    async def generate(self, question: str, verified_facts: Dict, history: List[Dict]) -> Tuple[str, str]:
        if not self.api_key:
            return await self.fallback.generate(question, verified_facts, history)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        contents = []
        for msg in history[-6:]:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        prompt_payload = (
            f"VERIFIED_BACKEND_FACTS (calculated in Python from authorized database records; no PII included):\n"
            f"{json.dumps(verified_facts, indent=2)}\n\n"
            f"TEACHER_QUESTION:\n{question}"
        )
        contents.append({"role": "user", "parts": [{"text": prompt_payload}]})

        body = {
            "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTIONS}]},
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 900,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(url, params={"key": self.api_key}, json=body)
                if resp.status_code == 429:
                    logger.warning("Gemini API rate limit (429) reached for model %s", self.model)
                    text, _ = await self.fallback.generate(question, verified_facts, history)
                    return (
                        text + "\n\n_(Gemini API rate limit reached; displayed grounded backend summary instead.)_",
                        "gemini-rate-limit-fallback",
                    )
                if resp.status_code >= 400:
                    logger.warning(
                        "Gemini API HTTP %s for model %s: %s",
                        resp.status_code,
                        self.model,
                        resp.text[:300],
                    )
                resp.raise_for_status()
                data = resp.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    return await self.fallback.generate(question, verified_facts, history)
                parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts).strip()
                if not text:
                    return await self.fallback.generate(question, verified_facts, history)
                return text, f"gemini:{self.model}"
        except Exception as exc:
            logger.warning("Gemini API request failed for model %s: %s", self.model, exc)
            text, _ = await self.fallback.generate(question, verified_facts, history)
            return (
                text + "\n\n_(Gemini API unavailable right now; displayed grounded backend summary instead.)_",
                "gemini-error-fallback",
            )


def get_llm_provider() -> BaseLLMProvider:
    if settings.GEMINI_API_KEY.strip():
        return GeminiLLMProvider(settings.GEMINI_API_KEY.strip(), settings.GEMINI_MODEL.strip())
    return DeterministicFallbackProvider()


def build_authorized_facts(db: Session, user: User, question: str) -> Dict:
    """
    Retrieve strictly authorized, PII-free facts from the database and compute
    all numerical statistics in Python before passing context to the LLM.
    """
    q_lower = question.lower()
    role_name = user.role_obj.name
    school_scope = user.assigned_school_id if role_name == "teacher" else None

    students_q = db.query(Student).options(joinedload(Student.school))
    if school_scope is not None:
        students_q = students_q.filter(Student.school_id == school_scope)
    elif role_name == "outreach" and user.assigned_worker_id:
        assigned_ids = [
            iv.student_id
            for iv in db.query(Intervention)
            .filter(Intervention.worker_id == user.assigned_worker_id)
            .all()
        ]
        students_q = students_q.filter(Student.id.in_(assigned_ids or ["__none__"]))

    authorized_students = students_q.all()
    authorized_ids = {s.id for s in authorized_students}

    assessments = {
        a.student_id: a
        for a in db.query(RiskAssessment).filter(RiskAssessment.is_current.is_(True)).all()
        if a.student_id in authorized_ids
    }

    facts: Dict = {
        "user_role": role_name,
        "scope_note": (
            f"Scoped to School {school_scope}"
            if school_scope is not None
            else ("Scoped to assigned outreach cases" if role_name == "outreach" else "Foundation-wide authorized view")
        ),
        "synthetic_data_notice": "Dataset A2 student records are synthetic illustrative records with no verified dropout labels.",
    }

    # Check if a specific Student ID (e.g. ST009) is mentioned
    st_matches = re.findall(r"\bST\d{3}\b", question.upper())
    if st_matches:
        target_id = st_matches[0]
        target = next((s for s in authorized_students if s.id == target_id), None)
        if target:
            ra = assessments.get(target.id)
            facts["student"] = {
                "student_id": target.id,
                "school_id": target.school_id,
                "attendance_pct": target.attendance_pct,
                "previous_term_score": target.previous_term_score,
                "distance_km": target.distance_km,
                "prior_intervention_count": target.prior_intervention_count,
                "risk": {
                    "priority_score": ra.priority_score,
                    "effective_band": ra.effective_band,
                    "validation_status": ra.validation_status,
                    "reason_codes": ra.reason_codes,
                    "missing_data_flags": ra.missing_data_flags,
                    "contributing_factors": ra.contributing_factors,
                    "recommended_next_step": ra.recommended_next_step,
                }
                if ra
                else None,
            }
        else:
            facts["access_notice"] = f"Student {target_id} is either not found or outside your role's authorized school/case scope."

    # Check if a specific School (e.g., School 7) is mentioned
    sc_matches = re.findall(r"school\s*#?(\d{1,2})", q_lower)
    if sc_matches:
        target_sc_id = int(sc_matches[0])
        if school_scope is None or school_scope == target_sc_id:
            sc = db.query(School).filter(School.id == target_sc_id).first()
            if sc:
                sc_students = [s for s in authorized_students if s.school_id == sc.id]
                facts["school_summary"] = {
                    "school_id": sc.id,
                    "code": sc.code,
                    "name": sc.name,
                    "enrolled_students": sc.enrolled_students,
                    "attendance_pct": sc.baseline_attendance_pct,
                    "tracked_students_count": len(sc_students),
                    "tracked_students": [
                        {
                            "student_id": s.id,
                            "attendance_pct": s.attendance_pct,
                            "previous_term_score": s.previous_term_score,
                            "distance_km": s.distance_km,
                        }
                        for s in sc_students
                    ],
                }

    # Priority queue summary
    ranked = []
    for s in authorized_students:
        ra = assessments.get(s.id)
        ranked.append(
            {
                "student_id": s.id,
                "school_id": s.school_id,
                "attendance_pct": s.attendance_pct,
                "previous_term_score": s.previous_term_score,
                "distance_km": s.distance_km,
                "prior_intervention_count": s.prior_intervention_count,
                "priority_score": ra.priority_score if ra else 0.0,
                "effective_band": ra.effective_band if ra else "Routine Review",
                "validation_status": ra.validation_status if ra else "pending_review",
            }
        )
    ranked.sort(key=lambda x: -x["priority_score"])
    facts["priority_students"] = ranked[:8]

    # School rankings (lowest attendance)
    if "school" in q_lower or "lowest" in q_lower or "attendance" in q_lower or "summary" in q_lower:
        schools_q = db.query(School).order_by(School.baseline_attendance_pct.asc())
        if school_scope is not None:
            schools_q = schools_q.filter(School.id == school_scope)
        facts["lowest_schools"] = [
            {
                "school_id": s.id,
                "code": s.code,
                "name": s.name,
                "enrolled_students": s.enrolled_students,
                "attendance_pct": s.baseline_attendance_pct,
            }
            for s in schools_q.limit(5).all()
        ]

    # Pending follow-ups & interventions
    int_q = db.query(Intervention).options(joinedload(Intervention.outcomes))
    if school_scope is not None:
        int_q = int_q.filter(Intervention.school_id == school_scope)
    elif role_name == "outreach" and user.assigned_worker_id:
        int_q = int_q.filter(Intervention.worker_id == user.assigned_worker_id)
    interventions = int_q.all()

    pending_followups = []
    for iv in interventions:
        if iv.status in ("pending", "rescheduled") or (
            iv.status == "completed"
            and (len(iv.outcomes) == 0 or any(o.follow_up_required and not o.follow_up_completed for o in iv.outcomes))
        ):
            pending_followups.append(
                {
                    "intervention_id": iv.id,
                    "student_id": iv.student_id,
                    "school_id": iv.school_id,
                    "status": iv.status,
                    "scheduled_date": iv.scheduled_date.isoformat(),
                    "note": "Outcome review or follow-up check-in due"
                    if iv.status == "completed"
                    else f"Scheduled {iv.intervention_type} ({iv.status})",
                }
            )
    facts["pending_followups"] = pending_followups[:10]

    # Impact & before/after summary
    if "outcome" in q_lower or "compare" in q_lower or "impact" in q_lower or "visit" in q_lower:
        imp = compute_impact_kpis(db, school_id=school_scope)
        facts["impact_summary"] = imp["outcome_analytics"]
        dash = compute_dashboard_summary(db, allowed_school_id=school_scope)
        facts["capacity_summary"] = {
            "weekly_visits_scheduled": dash["kpis"]["weekly_intervention_visits"],
            "max_weekly_visits": dash["kpis"]["max_weekly_visits"],
            "weekly_budget_used_inr": dash["kpis"]["weekly_budget_used_inr"],
            "weekly_budget_limit_inr": dash["kpis"]["weekly_budget_limit_inr"],
        }

    return facts


def validate_ai_response(response_text: str, verified_facts: Dict) -> str:
    """
    Verify that any ST### student IDs cited in the model response actually exist in
    the authorized facts payload; append a warning if an unknown ID is referenced.
    """
    allowed_ids = set()
    if "student" in verified_facts:
        allowed_ids.add(verified_facts["student"]["student_id"])
    for item in verified_facts.get("priority_students", []):
        allowed_ids.add(item["student_id"])
    for item in verified_facts.get("pending_followups", []):
        allowed_ids.add(item["student_id"])
    if "school_summary" in verified_facts:
        for item in verified_facts["school_summary"].get("tracked_students", []):
            allowed_ids.add(item["student_id"])

    mentioned_ids = set(re.findall(r"\bST\d{3}\b", response_text.upper()))
    unexpected = mentioned_ids - allowed_ids
    if unexpected:
        response_text += (
            f"\n\n> **Validation Guardrail Notice:** The identifiers {', '.join(sorted(unexpected))} "
            "were not part of your authorized query context and should not be acted upon."
        )
    return response_text


async def ask_teacher_assistant(
    db: Session,
    user: User,
    question: str,
    session_id: str,
) -> Dict:
    facts = build_authorized_facts(db, user, question)
    history_rows = (
        db.query(AssistantMessage)
        .filter(AssistantMessage.session_id == session_id, AssistantMessage.user_id == user.id)
        .order_by(AssistantMessage.created_at.asc())
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in history_rows]

    provider = get_llm_provider()
    raw_reply, provider_used = await provider.generate(question, facts, history)
    validated_reply = validate_ai_response(raw_reply, facts)

    user_msg = AssistantMessage(
        session_id=session_id,
        user_id=user.id,
        role="user",
        content=question,
    )
    bot_msg = AssistantMessage(
        session_id=session_id,
        user_id=user.id,
        role="assistant",
        content=validated_reply,
        verified_facts=facts,
        provider_used=provider_used,
    )
    db.add_all([user_msg, bot_msg])
    db.commit()

    return {
        "session_id": session_id,
        "reply": validated_reply,
        "provider_used": provider_used,
        "gemini_configured": bool(settings.GEMINI_API_KEY.strip()),
        "verified_facts": facts,
        "human_review_required": True,
    }