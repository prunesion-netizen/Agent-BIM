"""
compliance.py — Router conformitate ISO 19650 completă.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.sql_models import UserModel
from app.services.auth import get_current_user
from app.services.iso_compliance_checker import check_full_compliance
from app.services.project_health import compute_project_health
from app.services.pdf_report_exporter import generate_compliance_pdf
from app.repositories.projects_repository import get_project

router = APIRouter()


@router.get("/projects/{project_id}/iso-compliance")
def get_iso_compliance(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verifică conformitatea completă ISO 19650 pentru un proiect."""
    return check_full_compliance(db, project_id)


@router.get("/projects/{project_id}/export-compliance-pdf")
def export_compliance_pdf(
    project_id: int,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exportă raportul de conformitate ISO 19650 ca PDF."""
    project = get_project(db, project_id)
    if not project:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Proiectul nu exista.")

    compliance_data = check_full_compliance(db, project_id)
    health_data = compute_project_health(db, project_id)

    pdf_buffer = generate_compliance_pdf(
        compliance_data=compliance_data,
        health_data=health_data,
        project_name=project.name,
        project_code=project.code,
    )

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="ISO19650_Raport_{project.code}.pdf"'
        },
    )
