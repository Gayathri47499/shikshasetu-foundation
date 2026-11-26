from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.auth.security import require_roles
from app.database import get_db
from app.models.entities import ImportBatch, User
from app.services.csv_ingestion import commit_validated_csv, parse_and_validate_csv

router = APIRouter(prefix="/api/imports", tags=["Data Upload & Validation"])

SAMPLE_TEMPLATES = {
    "schools": "id,code,name,enrolled_students,baseline_attendance_pct,district\n11,SCH11,School 11,75,79,Rural East\n",
    "students": "id,school_id,attendance_pct,previous_term_score,distance_km,prior_intervention_count,grade_level\nST013,7,46,51,5.5,0,Grade 7\n",
    "attendance": "student_id,school_id,week_label,record_date,attendance_pct\nST009,7,2026-W47,2026-11-23,42\n",
    "academics": "student_id,term,score,assessment_type\nST009,Mid-Term 2026,46,Unit Assessment\n",
    "interventions": "student_id,school_id,scheduled_date,intervention_type,worker_id\nST009,7,2026-11-28,Household Visit,OW04\n",
}


@router.get("/history")
def get_import_history(
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    batches = db.query(ImportBatch).order_by(ImportBatch.created_at.desc()).limit(25).all()
    return {
        "batches": [
            {
                "id": b.id,
                "entity_type": b.entity_type,
                "filename": b.filename,
                "total_rows": b.total_rows,
                "valid_rows": b.valid_rows,
                "error_rows": b.error_rows,
                "status": b.status,
                "errors_summary": b.errors_summary,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in batches
        ]
    }


@router.get("/template/{entity_type}")
def download_csv_template(
    entity_type: str,
    current_user: User = Depends(require_roles("admin")),
):
    if entity_type not in SAMPLE_TEMPLATES:
        raise HTTPException(status_code=400, detail="Unsupported entity_type.")
    return StreamingResponse(
        iter([SAMPLE_TEMPLATES[entity_type]]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=template_{entity_type}.csv"},
    )


@router.post("/{entity_type}/preview")
async def preview_csv_import(
    entity_type: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")
    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded.") from exc

    result = parse_and_validate_csv(db, entity_type, text)
    return {k: v for k, v in result.items() if k != "valid_rows"}


@router.post("/{entity_type}/confirm")
async def confirm_csv_import(
    entity_type: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")
    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded.") from exc

    return commit_validated_csv(
        db=db,
        entity_type=entity_type,
        filename=file.filename or f"{entity_type}.csv",
        csv_text=text,
        actor=current_user,
    )
