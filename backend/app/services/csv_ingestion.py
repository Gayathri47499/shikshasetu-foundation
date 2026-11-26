import csv
import io
from datetime import date, datetime
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session

from app.auth.security import log_audit_event
from app.models.entities import (
    AcademicRecord,
    AttendanceRecord,
    ImportBatch,
    Intervention,
    Notification,
    OutreachWorker,
    School,
    Student,
    User,
)

REQUIRED_COLUMNS = {
    "schools": {"id", "name", "enrolled_students", "baseline_attendance_pct"},
    "students": {"id", "school_id", "attendance_pct", "distance_km"},
    "attendance": {"student_id", "school_id", "week_label", "record_date", "attendance_pct"},
    "academics": {"student_id", "term", "score"},
    "interventions": {"student_id", "school_id", "scheduled_date", "intervention_type"},
}


def parse_and_validate_csv(
    db: Session,
    entity_type: str,
    csv_text: str,
) -> Dict:
    """
    Validate uploaded CSV rows without silently discarding bad rows.
    Returns exact row-level errors, preview rows, and valid rows ready for confirmation.
    """
    if entity_type not in REQUIRED_COLUMNS:
        return {
            "entity_type": entity_type,
            "schema_valid": False,
            "missing_columns": [],
            "total_rows": 0,
            "valid_count": 0,
            "error_count": 1,
            "errors": [{"row": 0, "field": "entity_type", "message": f"Unsupported import type '{entity_type}'"}],
            "valid_rows": [],
            "preview_rows": [],
        }

    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    headers = {h.strip() for h in (reader.fieldnames or []) if h}
    required = REQUIRED_COLUMNS[entity_type]
    missing_cols = sorted(required - headers)
    if missing_cols:
        return {
            "entity_type": entity_type,
            "schema_valid": False,
            "missing_columns": missing_cols,
            "total_rows": 0,
            "valid_count": 0,
            "error_count": 1,
            "errors": [
                {
                    "row": 1,
                    "field": "header",
                    "message": f"Missing required column(s): {', '.join(missing_cols)}",
                }
            ],
            "valid_rows": [],
            "preview_rows": [],
        }

    existing_schools = {s.id for s in db.query(School.id).all()}
    existing_students = {s.id for s in db.query(Student.id).all()}
    existing_workers = {w.id for w in db.query(OutreachWorker.id).all()}

    seen_ids = set()
    valid_rows: List[Dict] = []
    errors: List[Dict] = []
    preview_rows: List[Dict] = []
    total_rows = 0

    for idx, raw_row in enumerate(reader, start=2):
        total_rows += 1
        row = {k.strip(): (v.strip() if v is not None else "") for k, v in raw_row.items() if k}
        row_errors: List[Tuple[str, str]] = []

        # Missing required value check
        for col in required:
            if not row.get(col):
                row_errors.append((col, f"Missing required value for '{col}'."))

        if entity_type == "schools" and not row_errors:
            try:
                sid = int(row["id"])
                enrolled = int(row["enrolled_students"])
                att = float(row["baseline_attendance_pct"])
                if sid in seen_ids:
                    row_errors.append(("id", f"Duplicate school id '{sid}' in CSV."))
                seen_ids.add(sid)
                if enrolled < 0:
                    row_errors.append(("enrolled_students", "Enrolled students cannot be negative."))
                if not (0.0 <= att <= 100.0):
                    row_errors.append(("baseline_attendance_pct", f"Invalid attendance {att}%; must be 0-100."))
                if not row_errors:
                    row["_parsed"] = {"id": sid, "enrolled": enrolled, "att": att}
            except ValueError:
                row_errors.append(("format", "id and enrolled_students must be integers; attendance must be numeric."))

        elif entity_type == "students" and not row_errors:
            sid = row["id"].upper()
            if sid in seen_ids:
                row_errors.append(("id", f"Duplicate student ID '{sid}' in CSV."))
            seen_ids.add(sid)
            try:
                sc_id = int(row["school_id"])
                att = float(row["attendance_pct"])
                dist = float(row["distance_km"])
                prev_score = float(row["previous_term_score"]) if row.get("previous_term_score") else None
                prior_cnt = int(row["prior_intervention_count"]) if row.get("prior_intervention_count") else 0
                if sc_id not in existing_schools:
                    row_errors.append(("school_id", f"Unknown school_id '{sc_id}'."))
                if not (0.0 <= att <= 100.0):
                    row_errors.append(("attendance_pct", f"Invalid attendance {att}%; must be between 0 and 100."))
                if prev_score is not None and not (0.0 <= prev_score <= 100.0):
                    row_errors.append(("previous_term_score", f"Score {prev_score} must be between 0 and 100."))
                if dist < 0:
                    row_errors.append(("distance_km", "Distance cannot be negative."))
                if not row_errors:
                    row["_parsed"] = {
                        "id": sid,
                        "school_id": sc_id,
                        "attendance_pct": att,
                        "distance_km": dist,
                        "previous_term_score": prev_score,
                        "prior_intervention_count": prior_cnt,
                    }
            except ValueError:
                row_errors.append(("format", "Numeric fields (school_id, attendance_pct, distance_km) have invalid values."))

        elif entity_type == "attendance" and not row_errors:
            sid = row["student_id"].upper()
            try:
                sc_id = int(row["school_id"])
                att = float(row["attendance_pct"])
                rec_date = date.fromisoformat(row["record_date"])
                if sid not in existing_students:
                    row_errors.append(("student_id", f"Unknown student_id '{sid}'."))
                if sc_id not in existing_schools:
                    row_errors.append(("school_id", f"Unknown school_id '{sc_id}'."))
                if not (0.0 <= att <= 100.0):
                    row_errors.append(("attendance_pct", f"Invalid attendance {att}%; must be 0-100."))
                if not row_errors:
                    row["_parsed"] = {
                        "student_id": sid,
                        "school_id": sc_id,
                        "week_label": row["week_label"],
                        "record_date": rec_date.isoformat(),
                        "attendance_pct": att,
                    }
            except ValueError:
                row_errors.append(("format", "Check record_date (YYYY-MM-DD), school_id (int), or attendance_pct (0-100)."))

        elif entity_type == "academics" and not row_errors:
            sid = row["student_id"].upper()
            try:
                score = float(row["score"])
                if sid not in existing_students:
                    row_errors.append(("student_id", f"Unknown student_id '{sid}'."))
                if not (0.0 <= score <= 100.0):
                    row_errors.append(("score", f"Invalid score {score}; must be 0-100."))
                if not row_errors:
                    row["_parsed"] = {
                        "student_id": sid,
                        "term": row["term"],
                        "score": score,
                        "assessment_type": row.get("assessment_type") or "Term Examination",
                    }
            except ValueError:
                row_errors.append(("score", "Score must be numeric (0-100)."))

        elif entity_type == "interventions" and not row_errors:
            sid = row["student_id"].upper()
            try:
                sc_id = int(row["school_id"])
                s_date = date.fromisoformat(row["scheduled_date"])
                w_id = row.get("worker_id") or None
                if sid not in existing_students:
                    row_errors.append(("student_id", f"Unknown student_id '{sid}'."))
                if sc_id not in existing_schools:
                    row_errors.append(("school_id", f"Unknown school_id '{sc_id}'."))
                if w_id and w_id not in existing_workers:
                    row_errors.append(("worker_id", f"Unknown worker_id '{w_id}'."))
                if not row_errors:
                    row["_parsed"] = {
                        "student_id": sid,
                        "school_id": sc_id,
                        "scheduled_date": s_date.isoformat(),
                        "intervention_type": row["intervention_type"],
                        "worker_id": w_id,
                    }
            except ValueError:
                row_errors.append(("format", "Check school_id (int) or scheduled_date (YYYY-MM-DD)."))

        if row_errors:
            for field, msg in row_errors:
                errors.append({"row": idx, "field": field, "message": msg, "raw": row})
        else:
            clean_row = {k: v for k, v in row.items() if k != "_parsed"}
            clean_row["_parsed"] = row["_parsed"]
            valid_rows.append(clean_row)

        if len(preview_rows) < 25:
            preview_rows.append(
                {
                    "row": idx,
                    "status": "error" if row_errors else "valid",
                    "data": {k: v for k, v in row.items() if k != "_parsed"},
                    "errors": [m for _, m in row_errors],
                }
            )

    return {
        "entity_type": entity_type,
        "schema_valid": True,
        "missing_columns": [],
        "total_rows": total_rows,
        "valid_count": len(valid_rows),
        "error_count": len(errors),
        "errors": errors,
        "valid_rows": valid_rows,
        "preview_rows": preview_rows,
    }


def commit_validated_csv(
    db: Session,
    entity_type: str,
    filename: str,
    csv_text: str,
    actor: User,
) -> Dict:
    """Re-validate and commit valid CSV rows; record import batch, notifications, and audit log."""
    validation = parse_and_validate_csv(db, entity_type, csv_text)

    if validation["valid_count"] == 0:
        batch = ImportBatch(
            entity_type=entity_type,
            filename=filename,
            total_rows=validation["total_rows"],
            valid_rows=0,
            error_rows=validation["error_count"],
            status="failed",
            errors_summary=validation["errors"][:50],
            uploaded_by_id=actor.id,
        )
        db.add(batch)
        db.add(
            Notification(
                target_role="admin",
                category="failed_upload",
                severity="warning",
                title=f"CSV Import Failed ({entity_type})",
                message=f"File '{filename}' had 0 valid rows and {validation['error_count']} error(s).",
                reference_type="import_batch",
                reference_id=filename,
            )
        )
        db.commit()
        return {"imported_count": 0, "batch_id": batch.id, "validation": validation}

    imported = 0
    for row in validation["valid_rows"]:
        p = row["_parsed"]
        if entity_type == "schools":
            existing = db.query(School).filter(School.id == p["id"]).first()
            if existing:
                existing.name = row["name"]
                existing.enrolled_students = p["enrolled"]
                existing.baseline_attendance_pct = p["att"]
            else:
                db.add(
                    School(
                        id=p["id"],
                        code=row.get("code") or f"SCH{p['id']:02d}",
                        name=row["name"],
                        district=row.get("district") or "Uploaded Cluster",
                        enrolled_students=p["enrolled"],
                        baseline_attendance_pct=p["att"],
                        data_source="csv_upload",
                    )
                )
            imported += 1

        elif entity_type == "students":
            existing = db.query(Student).filter(Student.id == p["id"]).first()
            if existing:
                existing.school_id = p["school_id"]
                existing.attendance_pct = p["attendance_pct"]
                existing.distance_km = p["distance_km"]
                if p["previous_term_score"] is not None:
                    existing.previous_term_score = p["previous_term_score"]
                existing.data_source = "csv_upload"
            else:
                db.add(
                    Student(
                        id=p["id"],
                        school_id=p["school_id"],
                        grade_level=row.get("grade_level") or "Grade 7",
                        attendance_pct=p["attendance_pct"],
                        previous_term_score=p["previous_term_score"],
                        distance_km=p["distance_km"],
                        prior_intervention_count=p["prior_intervention_count"],
                        is_synthetic_assessment=False,
                        data_source="csv_upload",
                    )
                )
            imported += 1

        elif entity_type == "attendance":
            rec_date = date.fromisoformat(p["record_date"])
            db.add(
                AttendanceRecord(
                    student_id=p["student_id"],
                    school_id=p["school_id"],
                    week_label=p["week_label"],
                    record_date=rec_date,
                    attendance_pct=p["attendance_pct"],
                    days_present=round(p["attendance_pct"] / 20),
                    days_scheduled=5,
                    data_source="csv_upload",
                )
            )
            # Update latest student attendance snapshot
            st = db.query(Student).filter(Student.id == p["student_id"]).first()
            if st:
                st.attendance_pct = p["attendance_pct"]
            imported += 1

        elif entity_type == "academics":
            db.add(
                AcademicRecord(
                    student_id=p["student_id"],
                    term=p["term"],
                    assessment_type=p["assessment_type"],
                    score=p["score"],
                    data_source="csv_upload",
                )
            )
            st = db.query(Student).filter(Student.id == p["student_id"]).first()
            if st:
                st.previous_term_score = p["score"]
            imported += 1

        elif entity_type == "interventions":
            db.add(
                Intervention(
                    student_id=p["student_id"],
                    school_id=p["school_id"],
                    worker_id=p["worker_id"],
                    intervention_type=p["intervention_type"],
                    scheduled_date=date.fromisoformat(p["scheduled_date"]),
                    status="pending",
                    approval_status="approved",
                    approved_by_id=actor.id,
                    data_source="csv_upload",
                )
            )
            imported += 1

    batch = ImportBatch(
        entity_type=entity_type,
        filename=filename,
        total_rows=validation["total_rows"],
        valid_rows=imported,
        error_rows=validation["error_count"],
        status="imported",
        errors_summary=validation["errors"][:50],
        uploaded_by_id=actor.id,
    )
    db.add(batch)
    log_audit_event(
        db,
        actor=actor,
        action="csv_import_committed",
        record_type=entity_type,
        record_id=filename,
        reason=f"Imported {imported} valid rows ({validation['error_count']} flagged rows excluded)",
    )
    db.commit()

    return {
        "imported_count": imported,
        "batch_id": batch.id,
        "validation": {k: v for k, v in validation.items() if k != "valid_rows"},
    }
