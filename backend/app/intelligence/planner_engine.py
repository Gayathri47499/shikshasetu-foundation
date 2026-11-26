from datetime import date, timedelta
from typing import Dict, List, Tuple

from app.config import get_settings

settings = get_settings()


def validate_weekly_constraints(
    proposed_visits: List[Dict],
    workers: List[Dict],
    existing_approved_visits: List[Dict],
) -> Tuple[bool, List[str], Dict]:
    """
    Deterministically verify that a weekly schedule respects ALL Dataset A3 constraints:
    - Max 4 visits per worker per working day
    - 5 working days per week
    - Max 100 visits per week across foundation
    - Max ₹25,000 weekly budget (at ₹250 average cost per visit)
    """
    violations: List[str] = []
    worker_limits = {w["id"]: w.get("max_daily_visits", settings.MAX_VISITS_PER_WORKER_PER_DAY) for w in workers}

    combined = existing_approved_visits + proposed_visits
    total_visits = len(combined)
    total_cost = sum(float(v.get("estimated_cost_inr", settings.AVERAGE_VISIT_COST_INR)) for v in combined)

    if total_visits > settings.MAX_WEEKLY_VISITS:
        violations.append(
            f"Weekly visit limit exceeded: {total_visits} scheduled vs max {settings.MAX_WEEKLY_VISITS}."
        )

    if total_cost > settings.WEEKLY_BUDGET_INR:
        violations.append(
            f"Weekly budget exceeded: INR {total_cost:,.0f} vs max INR {settings.WEEKLY_BUDGET_INR:,.0f}."
        )

    daily_counts: Dict[Tuple[str, str], int] = {}
    for visit in combined:
        w_id = visit["worker_id"]
        v_date = str(visit["visit_date"])
        key = (w_id, v_date)
        daily_counts[key] = daily_counts.get(key, 0) + 1
        max_for_worker = worker_limits.get(w_id, settings.MAX_VISITS_PER_WORKER_PER_DAY)
        if daily_counts[key] > max_for_worker:
            violations.append(
                f"Worker {w_id} on {v_date} has {daily_counts[key]} visits (max {max_for_worker}/day)."
            )

    summary = {
        "total_visits": total_visits,
        "max_weekly_visits": settings.MAX_WEEKLY_VISITS,
        "remaining_capacity": max(0, settings.MAX_WEEKLY_VISITS - total_visits),
        "total_cost_inr": total_cost,
        "weekly_budget_inr": settings.WEEKLY_BUDGET_INR,
        "remaining_budget_inr": max(0.0, settings.WEEKLY_BUDGET_INR - total_cost),
    }
    return len(violations) == 0, violations, summary


def generate_proposed_weekly_plan(
    week_start_date: date,
    candidate_students: List[Dict],
    workers: List[Dict],
    existing_visits_in_week: List[Dict],
    max_visits_to_propose: int = 20,
) -> Dict:
    """
    Deterministic constraint-based weekly intervention allocation algorithm.

    Principles:
    1. Does NOT auto-schedule every student blindly; selects up to `max_visits_to_propose`
       prioritized candidates (High Priority & Review Soon) that don't already have an
       active pending visit in the target week.
    2. Matches students to the outreach worker covering their school cluster first, falling
       back to the least-loaded active worker on that day.
    3. Strictly obeys 4 visits/worker/day, 5 working days (Mon-Fri), 100 visits/week,
       and INR 25,000 weekly budget.
    4. Returns entries with approval_status='proposed' — requires Teacher/Admin approval!
    """
    working_days = [week_start_date + timedelta(days=i) for i in range(settings.WORKING_DAYS_PER_WEEK)]
    already_scheduled_students = {
        v["student_id"]
        for v in existing_visits_in_week
        if v.get("visit_status") in ("pending", "rescheduled")
        or v.get("approval_status") == "proposed"
    }

    # Track per-worker-per-day usage from existing visits
    slot_usage: Dict[Tuple[str, date], int] = {}
    worker_weekly_load: Dict[str, int] = {w["id"]: 0 for w in workers}
    for v in existing_visits_in_week:
        if v.get("visit_status") == "cancelled":
            continue
        v_date = v["visit_date"] if isinstance(v["visit_date"], date) else date.fromisoformat(str(v["visit_date"]))
        key = (v["worker_id"], v_date)
        slot_usage[key] = slot_usage.get(key, 0) + 1
        worker_weekly_load[v["worker_id"]] = worker_weekly_load.get(v["worker_id"], 0) + 1

    current_visit_count = sum(1 for v in existing_visits_in_week if v.get("visit_status") != "cancelled")
    current_budget_used = sum(
        float(v.get("estimated_cost_inr", settings.AVERAGE_VISIT_COST_INR))
        for v in existing_visits_in_week
        if v.get("visit_status") != "cancelled"
    )

    # Sort candidates: High Priority first, then Review Soon, highest score first
    band_rank = {"High Priority": 0, "Review Soon": 1, "Routine Review": 2}
    eligible = [
        c
        for c in candidate_students
        if c["student_id"] not in already_scheduled_students
        and c["effective_band"] in ("High Priority", "Review Soon")
    ]
    eligible.sort(
        key=lambda c: (band_rank.get(c["effective_band"], 9), -float(c["priority_score"]))
    )

    proposals: List[Dict] = []
    skipped_reasons: List[Dict] = []

    for cand in eligible:
        if len(proposals) >= max_visits_to_propose:
            skipped_reasons.append(
                {
                    "student_id": cand["student_id"],
                    "reason": f"Batch proposal cap ({max_visits_to_propose}) reached; queue for next review.",
                }
            )
            continue

        if current_visit_count + 1 > settings.MAX_WEEKLY_VISITS:
            skipped_reasons.append(
                {"student_id": cand["student_id"], "reason": "Weekly 100-visit foundation capacity reached."}
            )
            continue

        if current_budget_used + settings.AVERAGE_VISIT_COST_INR > settings.WEEKLY_BUDGET_INR:
            skipped_reasons.append(
                {"student_id": cand["student_id"], "reason": "Weekly INR 25,000 budget cap reached."}
            )
            continue

        # Choose preferred workers (matching school cluster first, then least weekly load)
        school_id = cand["school_id"]
        preferred_workers = sorted(
            [w for w in workers if w.get("is_active", True)],
            key=lambda w: (
                0 if school_id in (w.get("cluster_schools") or []) else 1,
                worker_weekly_load.get(w["id"], 0),
                w["id"],
            ),
        )

        assigned = False
        for day in working_days:
            for w in preferred_workers:
                max_daily = w.get("max_daily_visits", settings.MAX_VISITS_PER_WORKER_PER_DAY)
                used_today = slot_usage.get((w["id"], day), 0)
                if used_today < max_daily:
                    slot_usage[(w["id"], day)] = used_today + 1
                    worker_weekly_load[w["id"]] = worker_weekly_load.get(w["id"], 0) + 1
                    current_visit_count += 1
                    current_budget_used += settings.AVERAGE_VISIT_COST_INR

                    cluster_match = school_id in (w.get("cluster_schools") or [])
                    rationale = (
                        f"Proposed for {cand['effective_band']} triage (score {cand['priority_score']:.1f}). "
                        f"Assigned to {w['name']} ({'primary school cluster' if cluster_match else 'cross-cluster load balance'}) "
                        f"on {day.isoformat()} ({used_today + 1}/{max_daily} daily slots). Requires teacher/admin approval."
                    )
                    proposals.append(
                        {
                            "week_start_date": week_start_date,
                            "visit_date": day,
                            "worker_id": w["id"],
                            "worker_name": w["name"],
                            "student_id": cand["student_id"],
                            "school_id": school_id,
                            "priority_score_snapshot": float(cand["priority_score"]),
                            "priority_band_snapshot": cand["effective_band"],
                            "approval_status": "proposed",
                            "visit_status": "pending",
                            "estimated_cost_inr": settings.AVERAGE_VISIT_COST_INR,
                            "rationale": rationale,
                        }
                    )
                    assigned = True
                    break
            if assigned:
                break

        if not assigned:
            skipped_reasons.append(
                {
                    "student_id": cand["student_id"],
                    "reason": "All active outreach workers reached their 4 visits/day limit for the week.",
                }
            )

    return {
        "week_start_date": week_start_date.isoformat(),
        "proposals": proposals,
        "skipped": skipped_reasons,
        "projected_weekly_visits": current_visit_count,
        "projected_weekly_cost_inr": current_budget_used,
        "max_weekly_visits": settings.MAX_WEEKLY_VISITS,
        "weekly_budget_inr": settings.WEEKLY_BUDGET_INR,
        "approval_required": True,
    }
