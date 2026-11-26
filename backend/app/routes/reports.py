import csv
import io
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.analytics.kpi_engine import compute_impact_kpis
from app.auth.security import get_current_user
from app.database import get_db
from app.models.entities import School, User
from app.services.pdf_report import generate_impact_pdf

router = APIRouter(prefix="/api/reports", tags=["Foundation Impact Reports"])


@router.get("/impact")
def get_impact_report(
    school_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    effective_school = (
        current_user.assigned_school_id
        if current_user.role_obj.name == "teacher" and current_user.assigned_school_id is not None
        else school_id
    )
    return compute_impact_kpis(db, school_id=effective_school, date_from=date_from, date_to=date_to)


@router.get("/impact/csv")
def download_impact_csv(
    school_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    effective_school = (
        current_user.assigned_school_id
        if current_user.role_obj.name == "teacher" and current_user.assigned_school_id is not None
        else school_id
    )
    data = compute_impact_kpis(db, school_id=effective_school, date_from=date_from, date_to=date_to)
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["kpi_id", "kpi_name", "value", "definition", "data_label"])
    for k in data["kpis"]:
        writer.writerow([k["id"], k["name"], k["value"], k["definition"], k["data_label"]])
    out.seek(0)
    return StreamingResponse(
        iter([out.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=shikshasetu_impact_kpis.csv"},
    )


@router.get("/impact/pdf")
def download_impact_pdf(
    school_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    effective_school = (
        current_user.assigned_school_id
        if current_user.role_obj.name == "teacher" and current_user.assigned_school_id is not None
        else school_id
    )
    data = compute_impact_kpis(db, school_id=effective_school, date_from=date_from, date_to=date_to)
    schools_q = db.query(School).order_by(School.id)
    if effective_school is not None:
        schools_q = schools_q.filter(School.id == effective_school)
    pdf_bytes = generate_impact_pdf(data, schools_q.all())
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=shikshasetu_impact_report.pdf"},
    )
