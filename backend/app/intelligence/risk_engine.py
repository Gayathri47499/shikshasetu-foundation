from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass(frozen=True)
class RiskScoringConfig:
    """
    Transparent, prototype operational prioritization weights (Design Assumptions).

    Important boundary:
    The supplied 12 student records (Dataset A2) are synthetic and contain NO verified
    dropout outcome labels. These weights create an explainable review-priority index
    for operational triage, NOT a calibrated probability of dropout.
    """

    attendance_max_weight: float = 40.0
    academic_max_weight: float = 30.0
    distance_max_weight: float = 20.0
    followup_max_weight: float = 10.0
    distance_reference_km: float = 10.0

    # Band thresholds
    high_priority_score_threshold: float = 60.0
    high_priority_attendance_floor: float = 50.0
    review_soon_score_threshold: float = 40.0
    review_soon_attendance_floor: float = 65.0

    version: int = 1


DEFAULT_CONFIG = RiskScoringConfig()


def evaluate_student_priority(
    student_id: str,
    attendance_pct: float,
    previous_term_score: Optional[float],
    distance_km: float,
    prior_intervention_count: int,
    pending_outcome_review_count: int = 0,
    attendance_trend_delta: Optional[float] = None,
    config: RiskScoringConfig = DEFAULT_CONFIG,
) -> Dict:
    """
    Compute a deterministic, fully explainable operational review-priority assessment.

    Safeguards implemented from the blueprint:
    1. Prior visits do NOT automatically increase a student's risk score; only an
       unreviewed/pending outcome follow-up adds a follow-up prompt weight.
    2. Distance is explicitly framed as a travel/logistics barrier, not low motivation.
    3. Missing inputs are surfaced in `missing_data_flags` instead of silent imputation.
    """
    missing_data_flags: List[str] = []
    contributing_factors: List[Dict] = []
    reason_codes: List[str] = []

    # 1. Attendance concern (0 to 40 pts)
    clamped_att = max(0.0, min(100.0, float(attendance_pct)))
    att_component = round(((100.0 - clamped_att) / 100.0) * config.attendance_max_weight, 2)
    trend_note = ""
    if attendance_trend_delta is None:
        missing_data_flags.append("No multi-week longitudinal attendance trend available")
    else:
        if attendance_trend_delta <= -5.0:
            att_component = min(config.attendance_max_weight, round(att_component + 4.0, 2))
            trend_note = f" (declined {abs(attendance_trend_delta):.1f}% across recent weeks)"
            reason_codes.append("ATT_DECLINING_TREND")

    if clamped_att < 50.0:
        reason_codes.append("ATT_CRITICALLY_LOW")
    elif clamped_att < 65.0:
        reason_codes.append("ATT_BELOW_THRESHOLD")

    contributing_factors.append(
        {
            "factor": "Attendance Concern",
            "value_display": f"{clamped_att:.0f}%{trend_note}",
            "points": att_component,
            "max_points": config.attendance_max_weight,
            "explanation": (
                f"Attendance is {clamped_att:.0f}% against an 80% target window."
                if clamped_att < 80.0
                else f"Attendance is {clamped_att:.0f}%, within healthy range."
            ),
            "caution": "Use comparable school calendar windows; attendance alone does not explain cause.",
        }
    )

    # 2. Academic indicator (0 to 30 pts)
    if previous_term_score is None:
        acad_component = 15.0  # neutral placeholder flagged as missing
        missing_data_flags.append("Previous term academic score is missing (neutral midpoint used)")
        reason_codes.append("ACAD_DATA_MISSING")
        acad_display = "Missing"
        acad_expl = "No previous term score on record; flagged for teacher verification."
    else:
        clamped_score = max(0.0, min(100.0, float(previous_term_score)))
        acad_component = round(((100.0 - clamped_score) / 100.0) * config.academic_max_weight, 2)
        acad_display = f"{clamped_score:.0f}/100"
        if clamped_score < 50.0:
            reason_codes.append("ACAD_LOW_PREV_SCORE")
            acad_expl = f"Previous term score ({clamped_score:.0f}/100) indicates learning support may help."
        elif clamped_score < 65.0:
            reason_codes.append("ACAD_MODERATE_SCORE")
            acad_expl = f"Previous term score ({clamped_score:.0f}/100) warrants periodic academic check-in."
        else:
            acad_expl = f"Previous term score ({clamped_score:.0f}/100) is satisfactory."

    missing_data_flags.append("No current-term formative score recorded for trend comparison")
    contributing_factors.append(
        {
            "factor": "Academic Indicator",
            "value_display": acad_display,
            "points": acad_component,
            "max_points": config.academic_max_weight,
            "explanation": acad_expl,
            "caution": "A single previous-term score is not a complete measure of student potential.",
        }
    )

    # 3. Access / logistics barrier (0 to 20 pts)
    clamped_dist = max(0.0, float(distance_km))
    dist_ratio = min(clamped_dist / config.distance_reference_km, 1.0)
    dist_component = round(dist_ratio * config.distance_max_weight, 2)
    if clamped_dist >= 6.0:
        reason_codes.append("ACCESS_LONG_DISTANCE")
        dist_expl = f"Home-to-school distance is {clamped_dist:.1f} km, indicating a potential travel/transport barrier."
    elif clamped_dist >= 4.0:
        reason_codes.append("ACCESS_MODERATE_DISTANCE")
        dist_expl = f"Home-to-school distance is {clamped_dist:.1f} km; check seasonal or transport constraints."
    else:
        dist_expl = f"Home-to-school distance is {clamped_dist:.1f} km (local proximity)."

    contributing_factors.append(
        {
            "factor": "Access & Travel Logistics",
            "value_display": f"{clamped_dist:.1f} km",
            "points": dist_component,
            "max_points": config.distance_max_weight,
            "explanation": dist_expl,
            "caution": "Distance reflects travel/access logistics, never low student motivation or family intent.",
        }
    )

    # 4. Intervention follow-up need (0 to 10 pts)
    if prior_intervention_count > 0 and pending_outcome_review_count > 0:
        followup_component = config.followup_max_weight
        reason_codes.append("FOLLOWUP_OUTCOME_PENDING")
        missing_data_flags.append(
            f"{pending_outcome_review_count} prior visit(s) lack a documented outcome review"
        )
        followup_expl = (
            f"{prior_intervention_count} prior visit(s) recorded with {pending_outcome_review_count} "
            "awaiting outcome verification before planning next steps."
        )
    elif prior_intervention_count > 0:
        followup_component = 0.0
        reason_codes.append("PRIOR_SUPPORT_LOGGED")
        followup_expl = (
            f"{prior_intervention_count} prior visit(s) recorded with documented follow-up; "
            "prior visits do not penalize the student."
        )
    else:
        followup_component = 0.0
        followup_expl = "No prior household interventions recorded yet."

    contributing_factors.append(
        {
            "factor": "Intervention Follow-up Status",
            "value_display": f"{prior_intervention_count} prior visit(s)",
            "points": followup_component,
            "max_points": config.followup_max_weight,
            "explanation": followup_expl,
            "caution": "Prior visits prompt outcome review and continuity; they do not automatically raise risk.",
        }
    )

    total_score = round(att_component + acad_component + dist_component + followup_component, 2)

    # Determine operational triage band
    if total_score >= config.high_priority_score_threshold or clamped_att < config.high_priority_attendance_floor:
        band = "High Priority"
    elif total_score >= config.review_soon_score_threshold or clamped_att < config.review_soon_attendance_floor:
        band = "Review Soon"
    else:
        band = "Routine Review"

    # Recommended non-stigmatizing next step
    if band == "High Priority" and pending_outcome_review_count > 0:
        next_step = (
            f"Review outcomes from {prior_intervention_count} prior visit(s) with the School Coordinator "
            "before scheduling a coordinated follow-up or transport/academic support check-in."
        )
    elif band == "High Priority":
        next_step = (
            "Teacher Coordinator review recommended within 48 hours to verify absence context and "
            "propose an outreach visit or school-based support plan."
        )
    elif band == "Review Soon":
        next_step = (
            "Schedule a brief teacher-student check-in and verify recent attendance context; "
            "queue for outreach only if barriers persist."
        )
    else:
        next_step = "Continue routine weekly attendance monitoring; no immediate outreach visit required."

    if not reason_codes:
        reason_codes.append("ROUTINE_MONITORING")

    return {
        "student_id": student_id,
        "version": config.version,
        "priority_score": total_score,
        "computed_band": band,
        "effective_band": band,
        "component_scores": {
            "attendance_concern": att_component,
            "academic_indicator": acad_component,
            "access_logistics": dist_component,
            "intervention_followup": followup_component,
        },
        "contributing_factors": contributing_factors,
        "reason_codes": reason_codes,
        "missing_data_flags": missing_data_flags,
        "recommended_next_step": next_step,
        "scoring_assumptions": asdict(config),
    }
